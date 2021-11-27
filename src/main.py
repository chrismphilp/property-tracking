import os

import datetime as dt
import pandas as pd
import google.cloud.logging
import google.auth

from rightmove import RightmovePropertiesForSale
from zoopla import ZooplaPropertiesForSale
from email_handler import EmailSender

from io import BytesIO
from flask import Flask
from google.cloud import secretmanager
from github import Github

# [START gae_python39_warmup_app]
# [START gae_python3_warmup_app]

app = Flask(__name__)

repository_name = os.environ.get("REPOSITORY", "REPOSITORY environment variable is not set.")

# Logging
client = google.cloud.logging.Client()
client.setup_logging()

# Secrets
secrets = secretmanager.SecretManagerServiceClient()
_, project_id = google.auth.default()
GITHUB_ACCESS_TOKEN = secrets.access_secret_version(request={"name": f"projects/{project_id}/secrets/github-access-token/versions/1"}).payload.data.decode("utf-8")

# GitHub
g = Github(GITHUB_ACCESS_TOKEN)


@app.route('/')
def main():
    repo = g.get_user().get_repo(repository_name)

    # Rightmove Properties
    repo_rightmove_csv = repo.get_contents("rightmove-houses.csv")
    parsed_rightmove_csv = pd.read_csv(BytesIO(repo_rightmove_csv.decoded_content))
    rightmove_csv = pd.concat([
        parsed_rightmove_csv,
        RightmovePropertiesForSale(location_identifier='REGION^93929', radius_from_location=0, ).parse_site(),  # barnet
        RightmovePropertiesForSale(location_identifier='REGION^1017', radius_from_location=1, ).parse_site(),  # northwood
        RightmovePropertiesForSale(location_identifier='REGION^1154', radius_from_location=1, ).parse_site(),  # ruislip
        RightmovePropertiesForSale(location_identifier='REGION^79781', radius_from_location=0.5, ).parse_site(),  # harrow_on_the_hill
    ])
    rightmove_csv['added_on'] = pd.to_datetime(rightmove_csv['added_on'], dayfirst=True)
    rightmove_csv = rightmove_csv.sort_values("added_on", ascending=False)
    rightmove_csv["added_on"] = rightmove_csv["added_on"].astype('str')

    rightmove_csv = rightmove_csv.drop_duplicates(subset=rightmove_csv.columns.difference(["search_datetime", "added_on"]), keep="first")
    rightmove_csv = rightmove_csv.to_csv(index=False)

    # Update Rightmove CSV
    rightmove_commit_message = f"Updating rightmove-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}"
    repo.update_file(path="rightmove-houses.csv", message=rightmove_commit_message, content=bytes(rightmove_csv, encoding='utf-8'), sha=repo_rightmove_csv.sha)

    # Zoopla Properties
    repo_zoopla_csv = repo.get_contents("zoopla-houses.csv")
    parsed_zoopla_csv = pd.read_csv(BytesIO(repo_zoopla_csv.decoded_content))
    zoopla_csv = pd.concat([
        parsed_zoopla_csv,
        ZooplaPropertiesForSale(location_identifier='barnet-london-borough', radius_from_location=0, include_sstc=False).parse_site(),  # barnet
        ZooplaPropertiesForSale(location_identifier='london/northwood', radius_from_location=1, include_sstc=False).parse_site(),  # northwood
        ZooplaPropertiesForSale(location_identifier='ruislip', radius_from_location=1, include_sstc=False).parse_site(),  # ruislip
        ZooplaPropertiesForSale(location_identifier='harrow-on-the-hill', radius_from_location=1, include_sstc=False).parse_site(),  # harrow-on-the-hill
    ])
    zoopla_csv['added_on'] = pd.to_datetime(zoopla_csv['added_on'], dayfirst=True)
    zoopla_csv = zoopla_csv.sort_values("added_on", ascending=False)
    zoopla_csv["added_on"] = zoopla_csv["added_on"].astype('str')

    zoopla_csv = zoopla_csv.drop_duplicates(subset=zoopla_csv.columns.difference(["search_datetime", "added_on"]), keep="first")
    zoopla_csv = zoopla_csv.to_csv(index=False)

    # Update Zoopla CSV
    zoopla_commit_message = f"Updating zoopla-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}"
    repo.update_file(path="zoopla-houses.csv", message=zoopla_commit_message, content=bytes(zoopla_csv, encoding='utf-8'), sha=repo_zoopla_csv.sha)

    # Send email
    EmailSender(rightmove_csv)

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
