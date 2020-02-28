import git
import os
import argparse


# initiate the parser
class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))


parser = argparse.ArgumentParser(description='this script will return the difference among biotools between branches',
                                 fromfile_prefix_chars="@")
parser.add_argument("path", help="path to metadata dir, e.g. /content/data/", type=str, action=readable_dir)
parser.add_argument("branch1", help="name of branch 1", type=str)
parser.add_argument("branch2", help="name of branch 1", type=str)
args = parser.parse_args()


def get_changeg_biotools(branch1, branch2, path):
    added_count = 0
    modified_count = 0
    deleted_count = 0
    format = '--name-status'
    files = []
    g = git.Git(path)
    differ = g.diff('%s..%s' % (branch1, branch2), format).split("\n")
    for line in differ:
        if len(line):
            files.append(line)

    for file in files:
        output_duple = file.split("	")
        file = os.path.basename(output_duple[1])
        dirname = os.path.basename(os.path.dirname(output_duple[1]))

        if (dirname + '.json' == file):
            if (output_duple[0] == 'A'):
                added_count += 1
            elif (output_duple[0] == 'D'):
                deleted_count += 1
            elif (output_duple[0] == 'M'):
                modified_count += 1
    return {'modified': modified_count, 'added': added_count, 'deleted': deleted_count}


statistics = get_changeg_biotools(args.branch1, args.branch2, args.path)
message = " BioTools affected:\n"
print(message, "added:", statistics['added'], "modified:", statistics['modified'], "deleted:", statistics['deleted'])
