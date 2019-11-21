import json
import os
import sys

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError as e:
    return False
  return True


if (len(sys.argv) != 2):
    print("error")
    exit()

root_folder = sys.argv[1].strip()


print("Succed by default")


#for root, dirs, files in os.walk(root_folder, topdown=False):
