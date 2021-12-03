# Property-Tracking

This application is deployed to `Google App Engine`, and is used to track property prices in certain areas within London for future reference. This can be deployed for **free** based
on the current gcloud pricing structure, and the locations can be set to any areas that either `Zoopla` or `Rightmove` currently accept.

A separate cron job on `gcloud` runs this main workflow every day at `5:30`, which generates an email containing the days properties in a basic `HTML` table, and updates the `CSV`
files within the repository.

Feel free to fork this for your own purposes.

## Personal Setup

### Prerequisites:

1) [GCloud account](https://console.cloud.google.com/)
2) [Github account](https://github.com/)
3) [SendGrid account](https://app.sendgrid.com/login?redirect_to=%2F)

### Setup

1) Generate a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) for `github`.
2) Generate a `SendGrid` [api key](https://app.sendgrid.com/login?redirect_to=%2Fsettings%2Fapi_keys).
3) Enable `Github Actions` for your repository to allow automatic deployments (*optional*).
    1) You will have to change the `app.yaml` `REPOSITORY` to match your own.
    2) Additionally, you will have to set up the following secrets in your `GitHub` repository`:
        1) `GCP_PROJECT` - your `gcloud` project ID
        2) `GCP_SA_KEY` - your `gcloud` service account key (stored in `base 64`)
4) [Set up the following secrets](https://cloud.google.com/sdk/gcloud/reference/secrets) in `gcloud`:
    1) `sendgrid-api-key` - containing your `SendGrid` api key
    2) `github-access-token` - containing your personal `GitHub` access token
    3) `from-email` - the email you want to show the email originated from (e.g. `myemail@email.com`)
    4) `to-email` - a comma delimited list of emails you want to send to (e.g. `myemail@email.com, youremail@email.com`)
5) Give each of the secrets `Secret Accessor` privileges to your `gcloud service account`.
6) [Set up](https://cloud.google.com/scheduler/docs/creating) a `cron` job to call your service periodically (*optional*).

### Disclaimer

*This is purely for educational purposes.*
