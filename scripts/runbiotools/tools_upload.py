#!/usr/bin/env python3
from datetime import datetime
import glob
import json
import logging
import argparse

import requests
from bs4 import BeautifulSoup

HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
HOST = 'http://localhost:8000/'

def login(user, password):
    payload = {'username':user,'password':password}
    response = requests.post(HOST+'api/rest-auth/login/', headers=HEADERS, json=payload)
    token = response.json()['key']
    return token

def run_upload(token):
    headers = HEADERS
    headers.update({'Authorization':f'Token {token}'})
    print(token)
    url = HOST + '/api/tool/validate/'
    #register tools
    for biotools_json_file in glob.glob('../content/data/*/*.biotools.json'):
        try:
            logging.debug(f'uploading {biotools_json_file}...')
            payload_dict=json.load(open(biotools_json_file))
            response = requests.post(url, headers=headers, json=payload_dict)
            response.raise_for_status()
            logging.debug(response.json())
            logging.debug(f'done uploading {biotools_json_file}')
        except requests.exceptions.HTTPError:
            soup = BeautifulSoup(response.text, "html.parser")
            messages = [','.join(error_el.contents) for error_el in soup.find_all(class_='exception_value')]
            logging.error(f'error while uploading {biotools_json_file} (status {response.status_code}): {"; ".join(messages)}')
            logging.error(f'request headers are: {headers}')
        except:
            logging.error(f'error while uploading {biotools_json_file}', exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bulk upload github tools to a test bio.tools server')
    parser.add_argument('login', type=str, help='bio.tools login')
    parser.add_argument('password', type=str, help='bio.tools password')
    args = parser.parse_args()
    token = login(args.login, args.password)
    run_upload(token)
