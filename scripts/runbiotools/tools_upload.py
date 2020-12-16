#!/usr/bin/env python3
from datetime import datetime
import glob
import json
import logging
import argparse

import requests
from bs4 import BeautifulSoup
from boltons.iterutils import remap

HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
HOST = 'http://localhost:8000/'

def login(user, password):
    payload = {'username':user,'password':password}
    response = requests.post(HOST+'api/rest-auth/login/', headers=HEADERS, json=payload)
    token = response.json()['key']
    return token

def run_upload(token, user):
    headers = HEADERS
    headers.update({'Authorization':f'Token {token}'})
    print(token)
    url = HOST + '/api/tool/validate/'
    #register tools
    tools_ok = []
    tools_ko = []
    for biotools_json_file in glob.glob('../content/data/*/*.biotools.json'):
        try:
            logging.debug(f'uploading {biotools_json_file}...')
            payload_dict=json.load(open(biotools_json_file))
            payload_dict["editPermission"]["authors"] = [user]
            payload_dict = remap(payload_dict, lambda p, k, v: k != 'term')
            response = requests.post(url, headers=headers, json=payload_dict)
            response.raise_for_status()
            tools_ok.append(payload_dict["biotoolsID"])
            logging.debug(response.json())
            logging.debug(f'done uploading {biotools_json_file}')
        except requests.exceptions.HTTPError:
            if response.status_code==500:
                soup = BeautifulSoup(response.text, "html.parser")
                messages = "; ".join([','.join(error_el.contents) for error_el in soup.find_all(class_='exception_value')])
            else:
                messages = response.text
            logging.error(f'error while uploading {biotools_json_file} (status {response.status_code}): {messages}')
            tools_ko.append(payload_dict["biotoolsID"])
        except:
            logging.error(f'error while uploading {biotools_json_file}', exc_info=True)
            tools_ko.append(payload_dict["biotoolsID"])
    logging.error('Tools upload finished')
    logging.error(f"Tools OK: {len(tools_ok)}")
    logging.error(f"Tools KO: {len(tools_ko)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bulk upload github tools to a test bio.tools server')
    parser.add_argument('login', type=str, help='bio.tools login')
    parser.add_argument('password', type=str, help='bio.tools password')
    args = parser.parse_args()
    token = login(args.login, args.password)
    run_upload(token, args.login)
