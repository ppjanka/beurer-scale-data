# Deployment Documentation

## Automated Deployment to Google Cloud App Engine

This repository is configured with GitHub Actions to automatically deploy the application to Google Cloud App Engine when changes are pushed to the `main` branch.

### Workflow Configuration

The deployment workflow is defined in `.github/workflows/deploy-to-gcloud.yml`.

### Required Secrets

The following repository secret must be configured in GitHub for the workflow to function:

- **`GCLOUD_SERVICE_KEY`**: JSON key file for a Google Cloud service account with the following permissions:
  - App Engine Admin (roles/appengine.appAdmin) or App Engine Deployer (roles/appengine.deployer)
  - Service Account User (roles/iam.serviceAccountUser)
  - Cloud Build Service Account (roles/cloudbuild.builds.builder) - if using Cloud Build

### How to Set Up the Service Account

1. In Google Cloud Console, create a service account or use an existing one
2. Grant the service account the necessary permissions (listed above)
3. Create a JSON key for the service account
4. In GitHub repository settings, go to Settings > Secrets and variables > Actions
5. Create a new repository secret named `GCLOUD_SERVICE_KEY`
6. Paste the entire contents of the JSON key file as the secret value

### Deployment Process

When code is pushed to the `main` branch:

1. The workflow checks out the code
2. Authenticates to Google Cloud using the service account key
3. Sets up the Google Cloud SDK
4. Deploys the application to App Engine using `gcloud app deploy`

The deployment is non-interactive (`--quiet` flag) and uses the configuration specified in `app.yaml`.

### Manual Deployment

To manually deploy the application, you can also use the gcloud CLI:

```bash
gcloud app deploy app.yaml --project=YOUR_PROJECT_ID
```

Make sure you're authenticated with `gcloud auth login` first.
