import json
import os
import sys
import requests

# Toy validating script
# In order for Travis CI to fail the 
# code has to fail or exit with status of 1
# e.g. exit(1)

user_pass = os.environ['BT_CRED']
bt_user = user_pass.split('||')[0]
print(bt_user)

http_settings = {

    'host_prod':'https://bio.tools/api',
    'host_local':'http://localhost:8000/api',
    'host_dev':'https://dev.bio.tools/api',
    'login': '/rest-auth/login/',
    'tool': '/t',
    'validate': '/validate',
    'json': '?format=json',
    'username': bt_user,
    'password': bt_pass

}


def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError as e:
    return False
  return True

def has_biotoolsID(tool):
  return tool.get('biotoolsID') != None

def validate_main(root_folder):
  for root, dirs, files in os.walk(root_folder, topdown=False):
    for file in files:
      if not(file.lower().endswith('.oeb.json')):
        with open(os.path.join(root, file), 'r') as file:
          json_data = file.read()
          if not(is_json(json_data)):
            print('JSON error')
            exit(1)
          data = json.loads(json_data) 
          if not(has_biotoolsID(data)):
            print('Tool from file', file.name, ' has no id')
            exit(1)

# if (len(sys.argv) != 2):
#     print("error")
#     exit(1)

# root_folder = sys.argv[1].strip()

def login_prod(http_settings):

    headers_token = {
        'Content-Type': 'application/json'
    }

    user = json.dumps({
        'username': http_settings['username'],
        'password': http_settings['password']
    })

    token_r = requests.post(http_settings['host_prod'] + http_settings['login'] + http_settings['json'], headers=headers_token, data=user)
    token = json.loads(token_r.text)['key']

    return token

def process_file_types(filename):
  #OpenEBench
  if filename.find('.oeb.') != -1:
    print('OpenEBench files, not for validation:', filename)

  #bio.tools
  if (
      filename.find('data/') != -1 and 
      filename.find('.json') != -1 and
      filename.find('.oeb.') == -1
  ):
    print('Need to validate:', filename)

for line in sys.stdin:
    process_file_types(line.strip())


print('Trying to login...')
print(login_prod(http_settings))