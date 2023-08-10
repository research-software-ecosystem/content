# Research Software Ecosystem (RSEc) contents repository
This repository contains the metadata aggregated for the Research Software Ecosystem (RSEc). The purpose of this repository is to act as a central place for the exchange of these metadata for multiple projects, including bio.tools, Biocontainers, Bioconda, OpenEBench, Debian Med, BIII.eu, etc.

# Contents outline
All software metadata are in the data folder of this repository, each software package/tool being in a distinct folder, which contains multiple files. Each of these files contains the metadata regarding the software coming from a specific resource, or reformatted in a specific format.

```
# Example for the contents of the 'fastqc' folder:
fastqc.biotools.json # metadata for the fastqc bio.tools entry (pulled by RSEc bot)
bioconda_fastqc.yaml # metadata for the bioconda fastqc package (pulled by RSEc bot)
biocontainers.yaml # metadata for the fastqc biocontainers image (pushed by biocontainers bot)
fastqc.oeb.metrics.json  # metadata for the OpenEBench fastqc package metrics (pulled by RSEc bot)
fastqc.debian.yaml  # metadata for the Debian Med fastqc package (pulled by RSEc bot)
fastqc.bioschemas.jsonld  # metadata for the fastqc package, converted from bio.tools metadata (pulled by RSEc bot)
```
