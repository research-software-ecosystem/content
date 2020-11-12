#!/usr/bin/env python

import json
import os
import yaml

import pickle
import argparse
from pathlib import Path

import jinja2

from collections import defaultdict


def fake(foo, **args):
    pass


def parse_biotools(directory):
    """
    Function to get biotools content data into memory.
    """
    data = dict()
    for root, dirs, files in os.walk(directory):
        excluded = ["raw.json", "oeb.json", "biocontainers.json"]
        for filename in files:
            if not filename.endswith(tuple(excluded)) and filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    biotools = json.load(f)
                    # print(biotools)
                    bio_id = biotools['biotoolsID'].lower()
                    data[bio_id] = {'data': biotools, 'path': filepath}
    return data


def parse_bioconda(directory):
    """
    Function to get bioconda content data into memory.
    """

    data = dict()
    # print(Path(directory).glob('./*/meta.yaml'))
    for p in Path(directory).glob('./*/meta.yaml'):
        # print(p.absolute())
        template = jinja2.Template(p.read_text())
        # print(template.render())
        conda = yaml.safe_load(template.render(
            {'os': os, 'compiler': fake, 'environ': '', 'cdt': fake, 'pin_compatible': fake, 'pin_subpackage': fake,
             'exact': fake}))
        extras = conda.get('extra', None)
        # if conda['package']['name'].strip() != 'deeptools':
        #    continue
        identifiers = defaultdict(list)
        if extras:
            ids = extras.get('identifiers', None)
            # print(ids)
            if ids:
                for id in ids:
                    n, c = id.split(':', 1)
                    identifiers[n].append(c)
        data[str(p.absolute())] = dict({'recipe': conda, 'ids': identifiers})
        # print(conda['package']['name'], str(identifiers))

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
    # return data


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
                # assert len(bio) == 1
                bio = bio[0].lower()
                path = os.path.join(content_path, bio)
                if not tools.get(bio, None):
                    print('None bio.tools entry', bio)
                    # if not os.path.exists(path):
                    #    os.mkdir(path)
                    # create_metadata(data, '%s/bioconda_%s.yaml' % (path, bio), bio)
                    continue
                create_metadata(data, '%s/bioconda_%s.yaml' % (path, bio), bio)
                # print(bio, name, tools[bio]['path'])
                continue


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))


parser = argparse.ArgumentParser(description='test', fromfile_prefix_chars="@")
parser.add_argument("biotools", help="path to metadata dir, e.g. content/data/", type=str, action=readable_dir)
parser.add_argument("bioconda", help="path to bioconda recipes, e.g. bioconda-recipes/recipes", type=str,
                    action=readable_dir)
args = parser.parse_args()
print(args)
if __name__ == '__main__':
    content_path = args.biotools

    if not os.path.exists('./tools_data.pkl'):
        tools = parse_biotools(args.biotools)
        pickle.dump(tools, open("./tools_data.pkl", "wb"))
    else:
        tools = pickle.load(open('./tools_data.pkl', 'rb'))
    if not os.path.exists('./conda_data.pkl'):
        conda = parse_bioconda(args.bioconda)
        pickle.dump(conda, open("./conda_data.pkl", "wb"))
    else:
        conda = pickle.load(open('./conda_data.pkl', 'rb'))

    merge(tools, conda, content_path)
