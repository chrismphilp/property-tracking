import os
import base64

import datetime as dt
from rightmove import RightmovePropertiesForSale
from zoopla import ZooplaPropertiesForSale
from flask import Flask
import google.cloud.logging
from google.cloud import secretmanager
from github import Github

# [START gae_python39_warmup_app]
# [START gae_python3_warmup_app]

app = Flask(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT", "GCP_PROJECT environment variable is not set.")
REPOSITORY_NAME = os.environ.get("REPOSITORY", "REPOSITORY environment variable is not set.")

# Google
client = google.cloud.logging.Client()
client.setup_logging()
secrets = secretmanager.SecretManagerServiceClient()

# GitHub
GITHUB_ACCESS_TOKEN = secrets.access_secret_version(
    request={"name": "projects/" + PROJECT_ID + "/secrets/github-access-token/versions/1"}).payload.data.decode("utf-8")
g = Github(GITHUB_ACCESS_TOKEN)


@app.route('/')
def main():
    # Rightmove Properties
    RightmovePropertiesForSale(location_identifier='REGION^93929', radius_from_location=0, )  # barnet
    RightmovePropertiesForSale(location_identifier='REGION^1017', radius_from_location=1, )  # northwood
    RightmovePropertiesForSale(location_identifier='REGION^1154', radius_from_location=1, )  # ruislip
    RightmovePropertiesForSale(location_identifier='REGION^79781', radius_from_location=0.5, )  # harrow_on_the_hill

    # Zoopla Properties
    ZooplaPropertiesForSale(location_identifier='barnet-london-borough', radius_from_location=0, include_sstc=False)  # barnet
    ZooplaPropertiesForSale(location_identifier='london/northwood', radius_from_location=1, include_sstc=False)  # northwood
    ZooplaPropertiesForSale(location_identifier='ruislip', radius_from_location=1, include_sstc=False)  # ruislip
    ZooplaPropertiesForSale(location_identifier='harrow-on-the-hill', radius_from_location=1, include_sstc=False)  # harrow-on-the-hill

    repo = g.get_user().get_repo(REPOSITORY_NAME)

    # Update Rightmove CSV
    rightmove_contents = repo.get_contents("rightmove-houses.csv")
    rightmove_csv_encoded = base64.b64encode(open("rightmove-houses.csv", "r"))
    rightmove_commit_message = f"Updating rightmove-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}"
    repo.update_file(path="rightmove-houses.csv", message=rightmove_commit_message, content=rightmove_csv_encoded, sha=rightmove_contents.sha)

    # Update Zoopla CSV
    zoopla_contents = repo.get_contents("rightmove-houses.csv")
    zoopla_csv_encoded = base64.b64encode(open("zoopla-houses.csv", "r"))
    zoopla_commit_message = f"Updating zoopla-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}"
    repo.update_file(path="zoopla-houses.csv", message=zoopla_commit_message, content=zoopla_csv_encoded, sha=zoopla_contents.sha)

    return '', 200, {}


@app.route('/_ah/warmup')
def warmup():
    # Handle your warmup logic here, e.g. set up a database connection pool
    return '', 200, {}


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

# [END gae_python3_warmup_app]
# [END gae_python39_warmup_app]
