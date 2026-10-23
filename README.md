<p align="center">
  <a href="https://research-software-ecosystem.org">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/research-software-ecosystem/graphics/main/RSEc_Logo_FULL_mono.png">
      <img src="https://raw.githubusercontent.com/research-software-ecosystem/graphics/main/RSEc_Logo_FULL_RGB.png" alt="ELIXIR Research Software Ecosystem (RSEc)" width="300">
    </picture>
  </a>
</p>

# Research Software Ecosystem (RSEc) metadata commons

This repository aggregates metadata about research software for exchange between registries, package repositories, container services, workflow platforms and benchmarking services. Records from different sources are grouped by software entry, with selected transformations into shared formats such as Bioschemas.

Metadata are stored in source-specific representations rather than a single repository-wide schema. The Git history records changes to the aggregated records; metadata retain the provenance and terms of their respective sources.

_Note_: the repository is still currently named `content` for historical reasons which are to be addressed in the future. Unless for technical purposes, this repository is the `metadata-commons` of the RSEc.

## Repository structure

- [`data/`](data/) — metadata grouped by software entry, with files for each source or representation.
- [`imports/`](imports/) — source-specific imported records.
- [`schemas/`](schemas/) — schemas used to validate selected metadata.
- [`report/`](report/) — generated coverage and ecosystem reports.
- [`doc/`](doc/) — technical notes and documentation.
- [`.github/workflows/`](.github/workflows/) — automation for imports, validation, transformations and reporting.

## Sources and maintenance

Sources include bio.tools, Bioconda, BioContainers, Bioconductor, Debian Med, Galaxy, WorkflowHub, OpenEBench and BIII.eu. GitHub Actions automate selected imports and transformations; the workflow definitions describe their schedules and processing steps.

The default branch of this repository is `master`. Many importers, converters, validators and dataset generators live in the separate [RSEc utilities repository](https://github.com/research-software-ecosystem/utils).

## Working with the utilities

For work involving the utilities, clone the repositories side by side using the names expected by the scripts and workflows:

```sh
mkdir rsec-workspace
cd rsec-workspace
git clone --branch master https://github.com/research-software-ecosystem/content.git content
git clone https://github.com/research-software-ecosystem/utils.git utils
```

Some utilities resolve paths relative to their working directory, such as `../../content/data/` from `utils/bioschemas-gen/`. Keep the `content` and `utils` directory names and run each utility from the directory specified in its instructions or the corresponding workflow. Install the dependencies required by that utility before running it.

These are independent Git repositories. Commit and update changes in each repository separately; `utils` is not a Git submodule of `content`.

## Contributing

Open an issue or pull request in the repository containing the relevant metadata or code. Target `master` for pull requests to this repository, and consult the [governance document](GOVERNANCE.md) and [code of conduct](CODE_OF_CONDUCT.md).

## Example metadata bundle

Each software entry has a directory under `data/`. File names identify the source or representation; the exact files available vary between entries. For example, `data/fastqc/` includes:

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
oras pull ghcr.io/research-software-ecosystem/metadata-commons-datasets:latest
sha256sum -c metadata-commons-datasets.tar.gz.sha256
tar -xzf metadata-commons-datasets.tar.gz
sha256sum -c datasets/SHA256SUMS
```

This is an OCI artifact, not a runnable container image. In addition to `latest`, each build is tagged with its ISO year and week (`YYYY-WW`). The archive contains the generated datasets and a per-file `SHA256SUMS` manifest. Publication uses the workflow's `GITHUB_TOKEN` with `packages: write` permission. The publisher uses the normal sibling checkout layout (`content` and `utils`), so no generator path rewriting is needed. It does not fetch a separate dump from the development BIII service. Dataset coverage follows the generators available in `utils/bioschemas-gen`.
