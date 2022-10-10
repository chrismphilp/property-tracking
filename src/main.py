import base64
import io
import os

import pytz
import datetime as dt
import pandas as pd

from rightmove import RightmovePropertiesForSale
from zoopla import ZooplaPropertiesForSale
from email_handler import EmailSender

from dotenv import load_dotenv
from flask import Flask
from github import Github

# [START gae_python39_warmup_app]
# [START gae_python3_warmup_app]

load_dotenv()
app = Flask(__name__)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "ENVIRONMENT environment variable is not set.")
REPOSITORY = os.environ.get("REPOSITORY", "REPOSITORY environment variable is not set.")

if (ENVIRONMENT == 'gcloud'):
    import google.cloud.logging
    import google.auth
    from google.cloud import secretmanager

    # Logging
    client = google.cloud.logging.Client()
    client.setup_logging()

    # Secrets
    secrets = secretmanager.SecretManagerServiceClient()
    _, project_id = google.auth.default()
    GITHUB_ACCESS_TOKEN = secrets.access_secret_version(request={"name": f"projects/{project_id}/secrets/github-access-token/versions/latest"}).payload.data.decode("utf-8")
else:
    GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN", "GITHUB_ACCESS_TOKEN environment variable is not set.")


print(ENVIRONMENT)
print(REPOSITORY)
print(GITHUB_ACCESS_TOKEN)


# GitHub
g = Github(GITHUB_ACCESS_TOKEN)


@app.route('/')
def main():

    repo = g.get_user().get_repo(REPOSITORY)

    london_tzinfo = pytz.timezone("Europe/London")
    yesterday = (dt.datetime.now(dt.timezone.utc).astimezone(london_tzinfo) - dt.timedelta(days=1)).strftime("%Y-%m-%d")

    yesterdays_rightmove_houses = process_csv(
        repo,
        pd.concat([
            RightmovePropertiesForSale(location_identifier='REGION^93929', radius_from_location=1, ).parse_site(),  # barnet
            RightmovePropertiesForSale(location_identifier='REGION^1017', radius_from_location=1, ).parse_site(),  # northwood
            RightmovePropertiesForSale(location_identifier='REGION^1154', radius_from_location=1, ).parse_site(),  # ruislip
            RightmovePropertiesForSale(location_identifier='REGION^79781', radius_from_location=0.5, ).parse_site(),  # harrow_on_the_hill
            RightmovePropertiesForSale(location_identifier='REGION^896', radius_from_location=1, ).parse_site(),  # maidenhead
            RightmovePropertiesForSale(location_identifier='REGION^311', radius_from_location=1, ).parse_site(),  # chesham
            RightmovePropertiesForSale(location_identifier='REGION^36', radius_from_location=1, ).parse_site(),  # amersham
            RightmovePropertiesForSale(location_identifier='REGION^5133', radius_from_location=1, ).parse_site(),  # burnham
            RightmovePropertiesForSale(location_identifier='REGION^23997', radius_from_location=1, ).parse_site(),  # taplow
            RightmovePropertiesForSale(location_identifier='REGION^1070', radius_from_location=0, ).parse_site(),  # pinner
        ]),
        "rightmove-houses.csv",
        f"Updating rightmove-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}",
        yesterday
    )

    yesterdays_zoopla_houses = process_csv(
        repo,
        pd.concat([
            ZooplaPropertiesForSale(location_identifier='barnet-london-borough', radius_from_location=1, ).parse_site(),  # barnet
            ZooplaPropertiesForSale(location_identifier='london/northwood', radius_from_location=1, ).parse_site(),  # northwood
            ZooplaPropertiesForSale(location_identifier='ruislip', radius_from_location=1, ).parse_site(),  # ruislip
            ZooplaPropertiesForSale(location_identifier='harrow-on-the-hill', radius_from_location=1, ).parse_site(),  # harrow-on-the-hill
            ZooplaPropertiesForSale(location_identifier='maidenhead', radius_from_location=1, ).parse_site(),  # maidenhead
            ZooplaPropertiesForSale(location_identifier='chesham', radius_from_location=1, ).parse_site(),  # chesham
            ZooplaPropertiesForSale(location_identifier='amersham', radius_from_location=1, ).parse_site(),  # amersham
            ZooplaPropertiesForSale(location_identifier='berkshire/burnham', radius_from_location=1, ).parse_site(),  # burnham
            ZooplaPropertiesForSale(location_identifier='taplow', radius_from_location=1, ).parse_site(),  # taplow
            ZooplaPropertiesForSale(location_identifier='pinner', radius_from_location=0, ).parse_site(),  # pinner
        ]),
        "zoopla-houses.csv",
        f"Updating zoopla-houses.csv - {dt.datetime.now().strftime('%d/%m/%Y')}",
        yesterday
    )

    # Send email
    EmailSender(pd.concat([yesterdays_rightmove_houses, yesterdays_zoopla_houses]))

    return '', 200, {}


def process_csv(repo, new_properties, path, commit_message, yesterday):
    repo_csv = repo.get_contents(path)
    encoded_blob_csv = repo.get_git_blob(repo_csv.sha)
    decoded_blob_csv = base64.b64decode(encoded_blob_csv.content).decode('utf-8')
    csv = pd.concat([
        pd.read_csv(io.StringIO(decoded_blob_csv), encoding_errors='replace'),
        new_properties
    ])

    csv['added_on'] = pd.to_datetime(csv['added_on'], dayfirst=True)
    csv = csv.sort_values("added_on", ascending=False)
    csv["added_on"] = csv["added_on"].astype('str')

    csv = csv.drop_duplicates(subset=csv.columns.difference(["search_datetime", "added_on"]), keep="first")
    yesterdays_properties = csv.loc[csv["added_on"] == yesterday]

    csv_format = csv.to_csv(index=False, encoding='utf-8')

    repo.update_file(path=path, message=commit_message, content=bytes(csv_format, encoding='utf-8'), sha=repo_csv.sha)

    return yesterdays_properties


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
