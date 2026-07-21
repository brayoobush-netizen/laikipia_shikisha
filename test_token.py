import requests
from requests.auth import HTTPBasicAuth

def get_access_token():
    consumer_key = "PRmAoi9bJDtOKGnlyhwFsg8jw2t6pDGKTlIYZFmcrAnrCZ8v"
    consumer_secret = "PGlaPM65AnUMIXZu8oIpoBtk77ufAoUi3Cwh9HmUZ69QkAtOaAbS7s46tHGHnK4A"
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

# Test it
print(get_access_token())
