import json
import os
import sys

# Toy validating script
# In order for Travis CI to fail the 
# code has to fail or exit with status of 1
# e.g. exit(1)

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

if (len(sys.argv) != 2):
    print("error")
    exit(1)

root_folder = sys.argv[1].strip()

print("All good by default.")

