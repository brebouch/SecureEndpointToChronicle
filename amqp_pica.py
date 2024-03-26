#!/usr/bin/env python3
#
#   AMQP Operations
#   Author: brebouch@cisco.com
#

r"""
This module provides functions for setting up an AMQP connection to Cisco Secure Endpoint
and the callback function to be executed when an event arrives.
"""

import json
import ssl

import pika

import chronicle


def callback(channel, method, properties, body):
    event = json.loads(body.decode())
    chronicle.post_event_data([event])


def consume_events(host, user_name, password, port, queue_name):
    amqp_url = f"amqps://{user_name}:{password}@{host}:{port}"
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    amqp_ssl = pika.SSLOptions(context)

    params = pika.URLParameters(amqp_url)
    params.ssl_options = amqp_ssl
    params.heartbeat = 30

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.basic_consume(
        queue_name,
        callback,
        auto_ack=False
    )

    channel.start_consuming()
