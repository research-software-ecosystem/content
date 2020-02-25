import requests
import json
import os
import sys
import argparse


def main(filters=None, limit=-1, dump=False):
    
    """
    Go through all bio.tools entries and produce an RDF graph representation (BioSchemas / JSON-LD).  
    :param limit: an integer value specifying the max number of entries to be crawled, -1 by default, means no limit.
    """
    
    i = 1
    nb_tools = 1
    has_next_page = True
    filters = filters or {}
    while has_next_page :
        parameters = {**filters, **{'page':i}}
        response = requests.get(
            'https://bio.tools/api/tool/',
            params=parameters,
            headers={'Accept': 'application/json'},
        )
        try:
            entry = response.json()
        except JSONDecodeError as e:
            print("Json decode error for " + str(req.data.decode('utf-8')))
            break
        has_next_page = (entry['next'] != None)

        for tool in entry['list']:
            tool_id = tool['biotoolsID']
            print(tool_id)
            nb_tools += 1
        i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='biotools to bioschemas bot script')
    parser.add_argument('collection', type=str, default='*', nargs='?',
                    help='collection name filter')
    args = parser.parse_args()
    if args.collection=='*':
        main(limit=-1, dump=True)
    else:
        main(filters={'collection':args.collection}, limit=-1, dump=True)

