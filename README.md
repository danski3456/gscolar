# Gscolar

A python utility to download all the relevant papers on a given topic and sort them based on citations, year. 

## Installation

Simply run:
```sh
./setup.sh
```

## Usage

Simply run 

```sh
./gscolar.py download <your query here>
```

You can then export the results to csv:

```sh
./gscolar.py get-csv <name of jsonl file generated in previous step>
```
