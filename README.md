# Website

This website is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

## Installation

- `npm i` for docusaurus

- `pip i -r requeriments.txt` for python scripts (first create an env)

> linux env: python -m venv .venv -> source .venv/bin/activate

## Run proyect

### Page

- npm start (develop in default language)
- npm run start -- --locale en (develop in English)

### Scripts

- python scripts/fetch_docs.py (u need a credentials json file)

## Build proyect

In order to enable multiple languages, the page must be built:

- npm run build

### serve built project

- npm run serve
