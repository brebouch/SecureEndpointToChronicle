# Secure Endpoint to Chronicle Event Exporter

## Overview
This tool is a work in progress effort example of creating an export client for Cisco Secure Endpoint events to Google Chronicle.

### Note
Please be aware this project is a proof of concept and is not expected to be used as a production application without due diligence.

## Requirements

1. API credentials to Cisco Secure Endpoint
   https://www.cisco.com/c/en/us/support/docs/security/amp-endpoints/201121-Overview-of-the-Cisco-AMP-for-Endpoints.html#anc1
2. A GCP Service Account with credentials file and access to Chronicles Ingest API
    https://cloud.google.com/chronicle/docs/reference/ingestion-api#getting_api_authentication_credentials
3. Compute resource with python3 installed

## Configuration

1. Clone the repository into the desired directory
2. cd into the cloned directory
3. Install dependencies, pip install -r requirements.txt
4. Copy the GCP Service Account JSON file into the app directory with the name service_account.json
5. Update .env file in app directory with the following
   * Secure Endpoint API Client ID
   * Secure Endpoint API Secret
   * AMQP Hostname
   * AMQP Username
   * AMQP Password
   * AMQP Stream Name
   * Chronicle Customer ID

## Deployment

1. If a Secure Endpoint Event Stream has not already been configured, create by running `python3 main.py create example_stream_name`
2. Update the .env file with the AMQP connection details to include:
   * AMQP Hostname
   * AMQP Username
   * AMQP Password
   * AMQP Stream Name
3. Start the Event Listener by running `python3 main.py serve`

An optional parameter following the serve command to define a polling interval in seconds. To use it, you would want to execute the script with the following: `python3 main.py serve -–polling_interval 60`

The AMQP session to listens for 30 seconds at a time before establishing a new connection. The polling interval adds the delay in-between the old session closing and new session generating. At startup, it would then establish the connection, listen for 30 seconds, close the connection, and then wait another 60 before opening a new one. If omitted, it will still listen for the 30 seconds but then immediately re-establish the AMQP connection.


## Testing

1. Once the Event Listener is running, from a Secure Endpoint protected computer or the Secure Endpoint console, initiate a scan for a device
2. Validate that the event is being seen from Google Chronicle

**Note** The event stream can be configured to filter certain events, make sure the event you are testing isn't filtered if you do not see the events in Google Chronicle following the test.