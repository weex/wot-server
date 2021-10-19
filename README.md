# Trust scoring proof-of-concept

After cloning, save [trustdeduplicated.csv](https://figshare.com/articles/dataset/The_Freenet_social_trust_graph_extracted_from_the_Web_of_Trust/4725664) to the root of the repo, then open it and delete its first row with the column headings. Then you can run the following to import it.

```
sqlite3 wot.db < freenet-wot.sql
sqlite3 wot.db
.mode csv
.separator ";"
.import trustdeduplicated.csv trusts
```

Setup with `pip install -r requirements.txt`.

Run with `python nxwot.py`

----

# Web of Trust Server
 
Server for federated Web of Trust.

Authenticated, pseudonymous user and content ratings


## Setup

```sh
cp default_settings.py settings.py       # then edit settings to fix path to code
sqlite3 main.db < schema.sql
```

## Usage

python3 server.py

## Testing

python -m test

## REST API

* All requests via HTTP GET except where noted.
* Data returned as JSON, formatted with indent=4 for now.

/ - returns basic info

/status - returns uptime and free space
