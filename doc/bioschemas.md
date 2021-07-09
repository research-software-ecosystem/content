# Bioschemas content

## Introduction
The following [GitHub Action](https://github.com/bio-tools/content/actions/runs/225548502/workflow) acts as a crawler to produce Bioschemas markup from [_bio.tools_](https://bio.tools). It is based on [this script](https://github.com/bio-tools/content/blob/master/scripts/bioschemas/biotools_to_bioschemas.py) which leverages  the [Bioschemas Tool profile](https://bioschemas.org/profiles/Tool/0.4-DRAFT-2019_07_19). 

This work has been initiated in Jan 2020 at the ELIXIR Tools Platform hackathon held in Paris. 

## Main realizations
- JSON-LD serialization in the _bio.tools_ "Content" repository (https://github.com/bio-tools/content). An example entry is available here: https://github.com/bio-tools/content/blob/master/data/adam/adam.bioschemas.jsonld
- this code is now integrated in _bio.tools_ through a REST API: http://bio.tools/api/jaspar?format=jsonld
- automation through GitHub Actions https://github.com/bio-tools/content/actions/runs/225548502 
- an experimental SPARQL endpoint (Virtuoso) to play with the dataset: https://134.158.247.157/sparql 

## Querying Bioschemas semantic annotations
Although Schema.org and Bioschemas metadata are focusing on findability through search engines, they can also be considered as knowledge graphs and queried with the SPARQL query language. 

Here are some sample queries: 
#### Query 1: Bioschemas properties used in _bio.tools_ (sorted: most used first)
```
SELECT ?p (COUNT(?s) AS ?count ) { ?s ?p ?o } GROUP BY ?p ORDER BY DESC(?count)
```
[Run this query](https://134.158.247.157/sparql?default-graph-uri=&query=SELECT+%3Fp+%28COUNT%28%3Fs%29+AS+%3Fcount+%29+%7B+%3Fs+%3Fp+%3Fo+%7D+GROUP+BY+%3Fp+ORDER+BY+DESC%28%3Fcount%29&format=text%2Fhtml&timeout=0&debug=on&run=+Run+Query+)

#### Query 2: First 100 tools with their operation and the associated EDAM definition and synonyms
```
SELECT  * WHERE {
?x rdf:type <http://schema.org/SoftwareApplication> ;
   <http://schema.org/name> ?name ; 
   <http://schema.org/featureList> ?feature .

?feature  <http://www.geneontology.org/formats/oboInOwl#hasDefinition> ?def ; 
         <http://www.geneontology.org/formats/oboInOwl#hasExactSynonym> ?syn .
} limit 100
```
[Run this query](https://134.158.247.157/sparql?default-graph-uri=&query=SELECT++*+WHERE+%7B%0D%0A%3Fx+rdf%3Atype+%3Chttp%3A%2F%2Fschema.org%2FSoftwareApplication%3E+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fname%3E+%3Fname+%3B+%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2FfeatureList%3E+%3Ffeature+.%0D%0A%0D%0A%3Ffeature++%3Chttp%3A%2F%2Fwww.geneontology.org%2Fformats%2FoboInOwl%23hasDefinition%3E+%3Fdef+%3B+%0D%0A+++++++++%3Chttp%3A%2F%2Fwww.geneontology.org%2Fformats%2FoboInOwl%23hasExactSynonym%3E+%3Fsyn+.%0D%0A%7D+limit+100&format=text%2Fhtml&timeout=0&debug=on&run=+Run+Query+)

#### Query 3 : Type of tools sorted by the number of citations
```
SELECT  ?type (COUNT(?c) AS ?citations) WHERE {
?x rdf:type <http://schema.org/SoftwareApplication> ;
   <http://schema.org/name> ?name ; 
   <http://schema.org/additionalType> ?type ;
   <http://schema.org/citation> ?c .
} 
GROUP BY ?type
ORDER BY DESC(?citations)
```
[Run this query](https://134.158.247.157/sparql?default-graph-uri=&query=SELECT++%3Ftype+%28COUNT%28%3Fc%29+AS+%3Fcitations%29+WHERE+%7B%0D%0A%3Fx+rdf%3Atype+%3Chttp%3A%2F%2Fschema.org%2FSoftwareApplication%3E+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fname%3E+%3Fname+%3B+%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2FadditionalType%3E+%3Ftype+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fcitation%3E+%3Fc+.%0D%0A%7D+%0D%0AGROUP+BY+%3Ftype%0D%0AORDER+BY+DESC%28%3Fcitations%29&format=text%2Fhtml&timeout=0&debug=on&run=+Run+Query+)

#### Query 4 : Type of tools sorted by the number of contributors
```
SELECT  ?type (COUNT(?c) as ?contributors) WHERE {
?x rdf:type <http://schema.org/SoftwareApplication> ;
   <http://schema.org/name> ?name ; 
   <http://schema.org/additionalType> ?type ;
   <http://schema.org/contributor> ?c .
} GROUP BY ?type
ORDER BY DESC(?contributors)
```
[Run this query](https://134.158.247.157/sparql?default-graph-uri=&query=SELECT++%3Ftype+%28COUNT%28%3Fc%29+as+%3Fcontributors%29+WHERE+%7B%0D%0A%3Fx+rdf%3Atype+%3Chttp%3A%2F%2Fschema.org%2FSoftwareApplication%3E+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fname%3E+%3Fname+%3B+%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2FadditionalType%3E+%3Ftype+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fcontributor%3E+%3Fc+.%0D%0A%7D+GROUP+BY+%3Ftype%0D%0AORDER+BY+DESC%28%3Fcontributors%29&format=text%2Fhtml&timeout=0&debug=on&run=+Run+Query+)

#### Query 5 : Most used licenses 
```
SELECT  ?license (COUNT(?license) as ?c) WHERE {
?x rdf:type <http://schema.org/SoftwareApplication> ;
   <http://schema.org/name> ?name ; 
   <http://schema.org/license> ?license .
} GROUP BY ?license
ORDER BY DESC(?c)
```
[Run this query](https://134.158.247.157/sparql?default-graph-uri=&query=SELECT++%3Flicense+%28COUNT%28%3Flicense%29+as+%3Fc%29+WHERE+%7B%0D%0A%3Fx+rdf%3Atype+%3Chttp%3A%2F%2Fschema.org%2FSoftwareApplication%3E+%3B%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Fname%3E+%3Fname+%3B+%0D%0A+++%3Chttp%3A%2F%2Fschema.org%2Flicense%3E+%3Flicense+.%0D%0A%7D+GROUP+BY+%3Flicense%0D%0AORDER+BY+DESC%28%3Fc%29&format=text%2Fhtml&timeout=0&debug=on&run=+Run+Query+)
