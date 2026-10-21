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

## Built dataset artifacts

Aggregate metadata dumps are generated weekly on Sunday at 08:00 UTC from `master` and published to GitHub Container Registry. The workflow can also be started manually. Each run starts with an empty datasets directory in its own runner checkout and executes the `*_dump.py` generators in the RSEc utilities repository. It does not commit generated dumps back to this repository. This publisher runs independently of the existing workflows, which continue generating and committing datasets as before.

Download the latest archive and its SHA-256 checksum with ORAS:

```sh
oras pull ghcr.io/research-software-ecosystem/content-datasets:latest
sha256sum -c content-datasets.tar.gz.sha256
tar -xzf content-datasets.tar.gz
sha256sum -c datasets/SHA256SUMS
```

This is an OCI artifact, not a runnable container image. In addition to `latest`, each build is tagged with its ISO year and week (`YYYY-WW`). The archive contains the generated datasets and a per-file `SHA256SUMS` manifest. Publication uses the workflow's `GITHUB_TOKEN` with `packages: write` permission. The publisher uses the normal sibling checkout layout (`content` and `utils`), so no generator path rewriting is needed. It does not fetch a separate dump from the development BIII service. Dataset coverage follows the generators available in `utils/bioschemas-gen`.
