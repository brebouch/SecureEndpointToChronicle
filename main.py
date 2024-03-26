import base64
import json
import os
import sys
from datetime import datetime, timedelta
import time

import requests
from dotenv import load_dotenv

import amqp_pica

load_dotenv()

base_url = "https://api.amp.cisco.com/v1"


def calculate_event_start_time(days=0):
    return str((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"))


def get_secure_endpoint_headers():
    u = os.environ.get('SECURE_ENDPOINT_API_CLIENT')
    p = os.environ.get('SECURE_ENDPOINT_API_KEY')
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode((u + ':' + p).encode()).decode()
    }


def secure_endpoint_get(url):
    resp = requests.get(url, headers=get_secure_endpoint_headers())
    if 199 < resp.status_code < 299:
        return resp.json()


def secure_endpoint_post(url, data):
    resp = requests.post(url, headers=get_secure_endpoint_headers(), data=json.dumps(data))
    if 199 < resp.status_code < 299:
        return resp.json()
    print(f'Error with api request, status code: {resp.status_code}\nError Message: {resp.text}')


def secure_endpoint_patch(url, data):
    resp = requests.patch(url, headers=get_secure_endpoint_headers(), data=json.dumps(data))
    if 199 < resp.status_code < 299:
        return resp.json()
    print(f'Error with api request, status code: {resp.status_code}\nError Message: {resp.text}')


def secure_endpoint_put(url, data):
    resp = requests.put(url, headers=get_secure_endpoint_headers(), data=json.dumps(data))
    if 199 < resp.status_code < 299:
        return resp.json()
    print(f'Error with api request, status code: {resp.status_code}\nError Message: {resp.text}')


def secure_endpoint_delete(url):
    resp = requests.delete(url, headers=get_secure_endpoint_headers())
    return resp.status_code


def get_secure_endpoint_events(**kwargs):
    uri = ''
    for k, v in kwargs.items():
        uri += f'{k}={v}&'
    url = f'{base_url}/events?{uri[:-1]}'
    return secure_endpoint_get(url)


def query_events(days=0):
    e = []
    resp = get_secure_endpoint_events(start_date=calculate_event_start_time(days=days))
    if resp:
        e += resp['data']
        total = resp['metadata']['results']['total']
        current_count = resp['metadata']['results']['current_item_count']
        index = resp['metadata']['results']['index'] + 1
        while len(e) < total:
            current_items = current_count * index
            r = get_secure_endpoint_events(start_date=calculate_event_start_time(days=days), offset=current_items)
            e += r['data']
            index += 1
    return e


def create_event_stream(stream_name):
    payload = {
        "name": stream_name}
    stream = secure_endpoint_post(f'{base_url}/event_streams', data=payload)
    if stream:
        with open('secure_endpoint_amqp.json', 'w') as stream_writer:
            stream_writer.write(json.dumps(json.dumps(stream)))
        print(f'Created Secure Endpoint Event Stream: {stream_name}\n')
        print(f'Event Stream ID: {stream["data"]["id"]}\n')
        print(f'update the .env file with the following:')
        print(f'AMQP_HOST="{stream["data"]["amqp_credentials"]["host"]}"')
        print(f'AMQP_USERNAME="{stream["data"]["amqp_credentials"]["user_name"]}"')
        print(f'AMQP_PASSWORD="{stream["data"]["amqp_credentials"]["password"]}"')
        print(f'AMQP_PORT="{stream["data"]["amqp_credentials"]["port"]}"')
        print(f'AMQP_STREAM_NAME="{stream["data"]["amqp_credentials"]["queue_name"]}"')


def get_event_stream(stream_name):
    response = secure_endpoint_get(f'{base_url}/event_streams')
    if response:
        for s in response['data']:
            if s['name'] == stream_name:
                return s


def list_event_stream():
    response = secure_endpoint_get(f'{base_url}/event_streams')
    if response:
        print('Current Event Streams:')
        print(json.dumps(response['data'], indent=4, sort_keys=True))
    else:
        print('No Event Streams')


def delete_event_stream(stream_name):
    stream = get_event_stream(stream_name)
    if stream:
        return secure_endpoint_delete(f'{base_url}/event_streams/{stream["id"]}')


if __name__ == '__main__':
    if sys.argv[1].lower() == 'list':
        list_event_stream()
    if len(sys.argv) != 3:
        if sys.argv[1].lower() == 'serve':
            polling_interval = 0
            if len(sys.argv) == 4:
                if sys.argv[2] == '--polling_interval':
                    try:
                        polling_interval = int(sys.argv[3])
                    except ValueError:
                        print('Polling interval must be an integer, using the default of 0')

            while True:
                try:
                    amqp_pica.consume_events(
                        os.environ.get('AMQP_HOST'),
                        os.environ.get('AMQP_USERNAME'),
                        os.environ.get('AMQP_PASSWORD'),
                        os.environ.get('AMQP_PORT'),
                        os.environ.get('AMQP_STREAM_NAME'),
                    )
                except Exception as e:
                    print(f'Caught exception: {e}\nRestarting Consumer')
                time.sleep(polling_interval)
        print('Invalid inputs provided')
        print('A action and event stream name must be provided as command line argument example '
              '"python3 main.py create test_stream"')
        sys.exit()
    if sys.argv[1].lower() == 'create':
        create_event_stream(sys.argv[2])
    elif sys.argv[1].lower() == 'delete':
        delete_event_stream(sys.argv[2])
        print('Successfully deleted')
    else:
        print('Invalid inputs provided')
        print('The only actions allowed are serve, create, or delete')
