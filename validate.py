import json
import os
import sys
import requests
from boltons.iterutils import remap
#from unidiff import PatchSet


# Toy validating script
# In order for Travis CI to fail the
# code has to fail or exit with status of 1
# e.g. exit(1)

user_pass = os.environ['BT_CRED']
bt_user = user_pass.split(',')[0]
bt_pass = user_pass.split(',')[1]

http_settings = {
    'host_prod': 'https://bio.tools/api',
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

    token_r = requests.post(http_settings['host_prod'] + http_settings['login'] +
                            http_settings['json'], headers=headers_token, data=user)
    token = json.loads(token_r.text)['key']

    return token

def tool_in_biotools(biotoolsID, http_settings):
    url = '{h}{t}/{id}{f}'.format(
        h=http_settings['host_prod'], t=http_settings['tool'], id=biotoolsID, v=http_settings['validate'], f=http_settings['json'])
    r = requests.get(url = url) 
    if r.status_code >= 200 and r.status_code <= 299:
        return True
    return False


def validate_tool_add(tool, token, http_settings):
    url = '{h}{t}{v}{f}'.format(
        h=http_settings['host_prod'], t=http_settings['tool'] ,v=http_settings['validate'], f=http_settings['json'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + token
    }

    r = requests.post(url, headers=headers, data=json.dumps(tool))
    if r.status_code >= 200 and r.status_code <= 299:
        return (True, r.text)

    return (False, r.text)


def validate_tool_update(tool, token, http_settings):
    url = '{h}{t}/{id}{v}{f}'.format(
        h=http_settings['host_prod'], t=http_settings['tool'], id=tool['biotoolsID'] ,v=http_settings['validate'], f=http_settings['json'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + token
    }

    r = requests.put(url, headers=headers, data=json.dumps(tool))
    if r.status_code >= 200 and r.status_code <= 299:
        return (True, r.text)

    return (False, r.text)

def validate_tool(tool, token, http_settings):
    # Maybe there is a way to know from git / GitHub
    # something like create file, update file
    # if the tool is new or not
    # for now we look at the id which is not optimal
    # the git request should somehow determine if it is 
    # a new tool or an existing tool
    if tool.get('biotoolsID') == None:
        print('No bio.tools id, validating adding tool...')
        return validate_tool_add(tool, token, http_settings)

    print('Checking if tool exists in bio.tools, with biotoolsID:',tool['biotoolsID'])
    if tool_in_biotools(tool['biotoolsID'], http_settings):
        print('Validating tool update for tool with biotoolsID:', tool['biotoolsID'])
        return validate_tool_update(tool, token, http_settings)
    else:
        print('Tool is not in bio.tools, trying to validate adding new tool with biotoolsID', tool['biotoolsID'])
        return validate_tool_add(tool, token, http_settings)
    


def read_tool(filename):
    with open(filename, 'r') as file:
        json_data = file.read()
        if not(is_json(json_data)):
            print('JSON error', filename)
            return None
        data = json.loads(json_data)
        return data
    return None
        


def is_bt_file_type(filename):
    # OpenEBench
    if filename.find('.oeb.') != -1:
        print('OpenEBench files, not for validation:', filename)
        return False

    # bio.tools
    if (
        filename.find('data/') != -1 and
        filename.find('.json') != -1 and
        filename.find('.oeb.') == -1
    ):
        print('bio.tools file, need to validate:', filename)
        return True
    
    print('Unknown file, not for validation', filename)
    return False
        
print('Started processing...')
print('Checking if any bio.tools files...')
bt_tool_files = []
# data = sys.stdin.read()
# patch = PatchSet(data)

# for p in patch:
#     print(p.source_file)
#     print(p.target_file)
#     print(p.is_added_file)
#     print(p.is_modified_file)
#     print(p.is_removed_file)
#     print('---------------')
#exit(0)
for line in sys.stdin:
    filename = line.strip()
    print('Checking file:<{f}>'.format(f=filename))
    is_bt = is_bt_file_type(filename)
    if is_bt:
        bt_tool_files.append(filename)

if len(bt_tool_files) == 0:
    print('No bio.tools files to process')
    print('DONE.')
    exit(0)

print('Found bio.tools files.')
print('Login in bio.tools ...')
token = login_prod(http_settings)
print('Logged in!')
print('Processing files...')

for filename in bt_tool_files:
    tool = read_tool(filename)
    if tool == None:
        print('Not a valid tool.')
        exit(1)
    drop_false = lambda path, key, value: bool(value)
    tool_cleaned = remap(tool, visit=drop_false)
    (valid, validation_text) = validate_tool(tool_cleaned, token, http_settings)
    if valid:
        print('Valid tool at:', filename)
    else:
        print('Invalid tool at:', filename)
        print('Error:', validation_text)
        exit(1)