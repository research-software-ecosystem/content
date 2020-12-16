import json
import ruamel.yaml as yaml
import argparse
import os
import sys


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
parser.add_argument("path", help="path to metadata dir, e.g. /content/data/", type=str, action=readable_dir)
args = parser.parse_args()


def enrich_dois(path):
    dirname = os.path.basename(os.path.normpath(path))
    file_types = {'json': '.json', 'yaml': '.yaml', 'debian': '.debian.yaml'}
    files = ["bioconda_" + dirname + file_types['yaml'], dirname + file_types['json'],
             dirname + file_types['debian']]
    files = [path + '/' + file for file in files if os.path.exists(path + '/' + file)]

    all_doies = set()
    json_dois = set()
    bioconda_dois = set()
    debian_dois = set()

    non_primary_dois = set()

    def parse_yaml(file):
        with open(file, 'r') as stream:
                return yaml.safe_load(stream)

    def parse_json(file):
        with open(file) as f:
            return json.load(f)

    def extract_doi_from_json(parsed_json):
        # if publication doesn't exist, return empty array
        if 'publication' in parsed_json:
            publications = parsed_json['publication']
            dois = set()
            for publication in publications:
                if ('type' in publication and 'doi' in publication and publication['type'] == 'Primary'):
                    dois.add(publication['doi'])
                elif ('type' in publication and 'doi' in publication and publication['type'] != 'Primary'):
                    non_primary_dois.add(publication['doi'])
            return dois
        else:
            return []

    def get_doi_identifiers_from_yaml(parsed_yaml, isDebian=False):
        if isDebian:
            # if doi entry exist return it, otherwise empty array
            print([item['value'] for item in parsed_yaml.get('bib', []) if item["key"]=="doi"])
            return [item['value'] for item in parsed_yaml.get('bib', []) if item["key"]=="doi"]
        if 'identifiers' in parsed_yaml:
            return filter(lambda identifier: 'doi' in identifier, parsed_yaml['identifiers'])

    def extract_doi_from_bioconda_yaml(parsed_yaml):
        # return it as list, so we can use len()
        return list(
            map(lambda identifier_doi: identifier_doi.split(':')[1], get_doi_identifiers_from_yaml(parsed_yaml)))

    def extract_doi_from_debian(parsed_yaml):
        dois = list(get_doi_identifiers_from_yaml(parsed_yaml, True))
        # if doi doesn't exist, return empty array
        if len(dois) == 0:
            return []
        return dois

    def write_dois_json(json_dois, file):
        parsed_json = parse_json(file)
        json_dois = json_dois.difference(non_primary_dois)
        if 'publication' not in parsed_json:
            parsed_json['publication'] = [{'doi': json_dois.pop(), 'type': 'Primary'}]

        publications = parsed_json['publication']
        for absent_doi in json_dois:
            publications.append({'doi': absent_doi, 'type': 'Primary'})
        parsed_json['publication'] = publications
        with open(file, 'w', encoding='utf-8') as outfile:
            json.dump(parsed_json, outfile, indent=4)

    def write_dois_bioconda(dois, file):
        parsed_yaml = parse_yaml(file)
        for doi in dois:
            parsed_yaml['identifiers'].append('doi:' + str(doi))
        with open(file, 'w') as outfile:
            yaml.safe_dump(parsed_yaml, outfile, default_flow_style=False)

    def write_dois_debian(dois, file):
        parsed_yaml = parse_yaml(file)
        identifiers = parsed_yaml['identifiers']
        # if doi doesn't exist
        if 'doi' not in identifiers:
            identifiers['doi'] = [dois.pop()]

        for doi in dois:
            identifiers['doi'].append(doi)

        parsed_yaml['identifiers'] = identifiers

        with open(file, 'w') as outfile:
            # do something fancy like indentation/mapping/sequence/offset
            yaml.safe_dump(parsed_yaml, outfile, default_flow_style=False)

    def enrich_files(method, dois, file):
        absent_dois = all_doies.difference(dois)
        if len(absent_dois):
            method(absent_dois, file)

    for file in files:
        dois = None
        if file.endswith(file_types['json']):
            parsed_json = parse_json(file)
            dois = extract_doi_from_json(parsed_json)
            json_dois = dois

        elif file.endswith(file_types['debian']):
            try:
                parsed_yaml = parse_yaml(file)
            except yaml.YAMLError as exc:
                print("unable to parse " + file, file=sys.stderr)
                print(exc, file=sys.stderr)
                files.remove(file)
                continue
            dois = extract_doi_from_debian(parsed_yaml)
            debian_dois = dois

        elif file.endswith(file_types['yaml']):
            parsed_yaml = parse_yaml(file)
            dois = extract_doi_from_bioconda_yaml(parsed_yaml)
            bioconda_dois = dois
        all_doies.update(dois)

    if len(all_doies) > 0:
        for file in files:
            if file.endswith(file_types['json']):
                enrich_files(write_dois_json, json_dois, file)

            elif file.endswith(file_types['debian']):
                enrich_files(write_dois_debian, debian_dois, file)

            elif file.endswith(file_types['yaml']):
                enrich_files(write_dois_bioconda, bioconda_dois, file)

[enrich_dois(f.path) for f in os.scandir(args.path) if f.is_dir()]
