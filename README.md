# Web of Trust Server
 
Server for Web of Trust.

Inspired by: [Scalable Moderation using a web-of-trust model](https://socialhub.activitypub.rocks/t/scalable-moderation-using-a-web-of-trust-model/2005)

Authenticated, pseudonymous user and content ratings

## Setup

```sh
pip install -r requirements.txt
cp default_settings.py settings.py       # then edit settings to fix path to code
sqlite3 main.db < schema.sql
```

## Usage

python3 server.py

## Testing

python -m test

## REST API

The API is defined in [openapi-spec.yaml](openapi-spec.yaml)

You can open this in an API tool like Insomnia or Postman for easy testing of a running server.py.
