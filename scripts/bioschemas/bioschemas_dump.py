import os
import glob
from rdflib import ConjunctiveGraph
from tabulate import tabulate

def get_bioschemas_files_in_repo():
    tools = []
    for data_file in glob.glob(r"../../data/*/*.bioschemas.jsonld"):
        #print(data_file)
        filename_ext = os.path.basename(data_file).split(".")
        if len(filename_ext) == 2 and filename_ext[1] == "jsonld":
            tools.append(data_file)
    return tools


def process_tools():
    """
    Go through all bio.tools entries in bioschemas JSON-LD and produce an single RDF file.
    """
    tool_files = get_bioschemas_files_in_repo()
    print(len(tool_files))
    rdf_graph = ConjunctiveGraph()

    for tool_file in tool_files:
        print(tool_file)
        rdf_graph.load(tool_file, format="json-ld")

    rdf_graph.serialize(
        format="turtle",
        destination="bioschemas-dump.ttl"
        #destination=os.path.join(directory, tpe_id + "bioschemas.jsonld")
    )

    show_stats(rdf_graph)

def show_stats(rdf_graph):
    """
    Display Bioschemas classes and properties counts.
    """

    ### display used classes
    classes_counts = """
    SELECT ?c (count(?c) as ?count) WHERE {
        ?s rdf:type ?c .
    } 
    GROUP BY ?p
    ORDER BY DESC(?c)
    """

    res = rdf_graph.query(classes_counts)
    print()
    print("Used ontology classes")
    print(tabulate(res))

    ### display used properties
    property_counts = """
    SELECT ?p (count(?p) as ?count) WHERE {
        ?s ?p ?o .
    } 
    GROUP BY ?p
    ORDER BY DESC(?count)
    """

    res = rdf_graph.query(property_counts)
    print()
    print("Used ontology properties")
    print(tabulate(res))

if __name__ == "__main__":
    process_tools()
