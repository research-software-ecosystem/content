#!/usr/bin/env python

import json
import os
import yaml

import pickle

#from ruamel.yaml import YAML
from pathlib import Path

import jinja2

from jinja2 import Environment
from collections import defaultdict

def fake(foo, **args):
    pass

def parse_biotools(directory):
    """
    Function to get biotools content data into memory.
    """
    data = dict()
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not filename.endswith("oeb.json") and filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    biotools = json.load(f)
                    bio_id = biotools['biotoolsID'].lower()
                    data[bio_id] = {'data': biotools, 'path': filepath}
    return data

def parse_bioconda(directory):
    """
    Function to get bioconda content data into memory.
    """

    data = dict()
    for p in Path(directory).glob('./*/meta.yaml'):
        #print(p.absolute())
        template = jinja2.Template(p.read_text())
        #print(template.render())
        conda = yaml.safe_load(template.render({'os': os, 'compiler': fake, 'environ': '', 'cdt': fake, 'pin_compatible': fake, 'pin_subpackage': fake, 'exact': fake}))
        extras = conda.get('extra', None)
        #if conda['package']['name'].strip() != 'deeptools':
        #    continue
        identifiers = defaultdict(list)
        if extras:
            ids = extras.get('identifiers', None)
            print(ids)
            #print(ids)
            if ids:
                for id in ids:
                    n, c = id.split(':', 1)
                    identifiers[n].append(c)
        data[str(p.absolute())] = dict({'recipe': conda, 'ids': identifiers})
        #print(conda['package']['name'], str(identifiers))

    return data
    """

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename == "meta.yaml":
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    conda = yaml.load(Environment().from_string(content).render())
                    ##conda = yaml.load(f)
                    print(conda['package']['name'])
                    data[filepath] = conda
    """
    #return data

def create_metadata(conda, path, biotools_id):
    data = conda['recipe']['package']
    data.update(conda['recipe']['about'])
    extra = conda['recipe'].get('extra', None)
    if extra:
        print('####', extra)
        identifiers = extra.get('identifiers', None)
        if extra.get('identifiers', None):
            data.update({'identifiers': extra['identifiers']})
    data.update({'biotools_id': biotools_id})
    with open(path, 'w') as out:
        yaml.dump(data, out)


def merge(tools, conda, content_path):
    for name, data in conda.items():
        ids = data['ids']
        if ids:
            bio = ids.get('biotools', None)
            if bio:
                # fix me ... recipes with multiple biotools, ids
                #assert len(bio) == 1
                bio = bio[0].lower()
                path = os.path.join(content_path, bio)
                if not tools.get(bio, None):
                    print('None bio.tools entry', bio)
                    #if not os.path.exists(path):
                    #    os.mkdir(path)
                    #create_metadata(data, '%s/bioconda_%s.yaml' % (path, bio), bio)
                    continue
                create_metadata(data, '%s/bioconda_%s.yaml' % (path, bio), bio)
                #print(bio, name, tools[bio]['path'])
                continue

if __name__ == '__main__':
    content_path = '/home/bag/projects/code/content/data'

    if not os.path.exists('./tools_data.pkl'):
        tools = parse_biotools('/home/bag/projects/code/content/data')
        pickle.dump(tools, open( "./tools_data.pkl", "wb" ))
    else:
        tools = pickle.load(open('./tools_data.pkl', 'rb'))
    if not os.path.exists('./conda_data.pkl'):
        conda = parse_bioconda('/home/bag/projects/code/bioconda-recipes/recipes')
        pickle.dump(conda, open( "./conda_data.pkl", "wb" ))
    else:
        conda = pickle.load(open('./conda_data.pkl', 'rb'))
    merge(tools, conda, content_path)

