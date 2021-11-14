from rightmove import RightmovePropertiesForSale
from zoopla import ZooplaPropertiesForSale
from flask import Flask

# [START gae_python39_warmup_app]
# [START gae_python3_warmup_app]
app = Flask(__name__)


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
