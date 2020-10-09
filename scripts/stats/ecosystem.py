import glob
import os


from matplotlib import pyplot
import pandas as pd
from upsetplot import plot

class Source(object):

    def __init__(self, entry):
        self.entry = entry
        self.biotools_id = self.entry.biotools_id
        if not self.SOURCE_PATH_TEMPLATE:
            raise NotImplementedError(self.entry)
        else:
            self.path = os.path.join(self.entry.repository.contents_data_path, self.biotools_id, self.SOURCE_PATH_TEMPLATE.format(biotools_id=self.biotools_id))
    
    def is_available(self):
        return os.path.isfile(self.path)


class BioToolsSource(Source):
    SOURCE = 'biotools'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.biotools.json'


class BioSchemasSource(Source):
    SOURCE = 'bioschemas'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.bioschemas.jsonld'


class OEBSource(Source):
    SOURCE = 'OEB'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.oeb.json'


class OEBMetricsSource(Source):
    SOURCE = 'OEB Metrics'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.oeb.metrics.json'


class DebianSource(Source):
    SOURCE = 'Debian'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.debian.yaml'


class BioCondaSource(Source):
    SOURCE = 'BioConda'
    SOURCE_PATH_TEMPLATE = 'bioconda_{biotools_id}.yaml'


class BioContainersSource(Source):
    SOURCE = 'BioContainers'
    SOURCE_PATH_TEMPLATE = 'biocontainers.json'

class BiiiSource(Source):
    SOURCE = 'Biii'
    SOURCE_PATH_TEMPLATE = '{biotools_id}.neubias.raw.json'


SOURCE_CLASSES = [
    BioToolsSource,
    BioSchemasSource,
    OEBSource,
    OEBMetricsSource,
    DebianSource,
    BioCondaSource,
    BioContainersSource,
    BiiiSource
]


class Entry(object):

    def __init__(self, repository, name):
        self.repository = repository
        self.name = name
        self.biotools_id = name
        self.sources = {}
        for source_class in SOURCE_CLASSES:
            self.sources[source_class.SOURCE] = source_class(self)


class Repository(object):

    def __init__(self, path):
        self.path = path
        self.contents_data_path = os.path.join(self.path,'data')
        self.entries = []

    def load(self):
        for folder in glob.glob(os.path.join(self.contents_data_path, '*')):
            biotools_id = os.path.basename(os.path.normpath(folder))
            entry = Entry(self, biotools_id)
            self.entries.append(entry)

    def generate_counts(self):
        rows = {}
        for entry in self.entries:
            rows[entry.biotools_id] = [source.is_available() for source in entry.sources.values()]
        df = pd.DataFrame.from_dict(rows, orient='index', columns=[source_class.SOURCE for source_class in SOURCE_CLASSES])
        print(df)
        print(df.groupby([source_class.SOURCE for source_class in SOURCE_CLASSES]).size().reset_index(name='Count') )
        plot(df.groupby([source_class.SOURCE for source_class in SOURCE_CLASSES]).size(), show_counts=True)
        pyplot.savefig('global_upset.png')

if __name__ == "__main__":
    repo = Repository('../..')
    repo.load()
    for entry in repo.entries:
        print(f"{entry.biotools_id : <100}: {'|'.join(['✓' if source.is_available() else '🗙' for source in entry.sources.values()])}")
    repo.generate_counts()
