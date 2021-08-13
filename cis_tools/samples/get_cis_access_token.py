import pprint

import requests

# get a bearer token when provided a client_id and client_secret

client_id = ""
client_secret = ""

headers = {
    "content-type": "application/json",
}

data = (
    '{"client_id":"'
    + client_id
    + '","client_secret":"'
    + client_secret
    + '","audience":"api.sso.mozilla.com","grant_type":"client_credentials"}'
)

response = requests.post(
    "https://auth.mozilla.auth0.com/oauth/token",
    headers=headers,
    data=data,
)
pprint.pprint(response.text)
