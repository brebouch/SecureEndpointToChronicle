#!/usr/bin/env python3
#
#   Cronicle Operations
#   Author: brebouch@cisco.com
#

r"""
This module provides functions for sending Cisco Secure Endpoint Events to Google Chronicle.
It is based of the example provides at:
https://github.com/chronicle/api-samples-python/blob/master/ingestion/create_unstructured_log_entries.py
"""

# Imports required for the sample - Google Auth and API Client Library Imports.
# Get these packages from https://pypi.org/project/google-api-python-client/ or run $ pip
# install google-api-python-client from your terminal
from google.oauth2 import service_account
from googleapiclient import _auth
import json
import os
from dotenv import load_dotenv

load_dotenv()


def get_chronicle_client():
    SCOPES = ['https://www.googleapis.com/auth/malachite-ingestion']

    # The apikeys-demo.json file contains the customer's OAuth 2 credentials.
    # SERVICE_ACCOUNT_FILE is the full path to the apikeys-demo.json file
    # ToDo: Replace this with the full path to your OAuth2 credentials
    SERVICE_ACCOUNT_FILE = './service_account.json'

    # Create a credential using Google Developer Service Account Credential and Chronicle API
    # Scope.
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Build an HTTP client to make authorized OAuth requests.
    http_client = _auth.authorized_http(credentials)
    return http_client


def transform_event_data(event):
    ips = []
    macs = []
    e = {
        "metadata":
            {
                "eventTimestamp": event['date'],
                "eventType": 'FILE_UNCATEGORIZED'
            },
        "additional":
            {
                "id": event['id']
            },
        "principal":
            {
                "hostname": event['computer']['hostname']
            }
    }
    if 'external_ip' in event['computer'].keys():
        ips.append(event['computer']['external_ip'])
    for n in event['computer']['network_addresses']:
        ips.append(n['ip'])
        macs.append(n['mac'])
    e['principal']['ip'] = ips
    e['principal']['mac'] = macs
    '''
    if 'file' in event.keys():
        e['file'] = {
            'full_path': event['file']['file_path'],
            'name': event['file']['file_name'],
            'md5': event['file']['identity']['md5'],
            'sha1': event['file']['identity']['sha1'],
            'sha256': event['file']['identity']['sha256']
        }
    if 'tactics' in event.keys():
        e.update({'attack_details': {'tactic': []}})
        for t in event['tactics']:
            e['attack_details']['tactic'].append({'id': t})
    if 'techniques' in event.keys():
        e.update({'attack_details': {'techniques': []}})
        for t in event['techniques']:
            e['attack_details']['techniques'].append({'id': t})
    '''
    return e


def create_logs(http_session, log_type, customer_id, log_text) -> None:
    """Sends unstructured log entries to the Chronicle backend for ingestion.

  Args:
    http_session: Authorized session for HTTP requests.
    log_type: Log type for a feed. To see supported log types run
      list_supported_log_types.py
    customer_id: A string containing the UUID for the Chronicle customer.
    logs_text: A string containing logs delimited by new line characters. The
      total size of this string may not exceed 1MB or the resultsing request to
      the ingestion API will fail.

  Raises:
    requests.exceptions.HTTPError: HTTP request resulted in an error
      (response.status_code >= 400).
  """
    INGESTION_API_BASE_URL = "https://malachiteingestion-pa.googleapis.com"
    url = f"{INGESTION_API_BASE_URL}/v2/unstructuredlogentries:batchCreate"
    body = {
        "customer_id": customer_id,
        "log_type": log_type,
        "namespace": "Cisco AMP",
        "entries": [
            {"logText": json.dumps(log_text)}
        ],
    }

    response = http_session.request(url, "POST", body=json.dumps(body))
    return response


def post_event_data(events):
    client = get_chronicle_client()
    for e in events:
        create_logs(client, 'CISCO_AMP', os.environ.get('CHRONICLE_CUSTOMER_ID'), e)
