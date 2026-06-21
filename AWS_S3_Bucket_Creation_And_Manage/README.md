# Monitor and Manage S3 Buckets

A Flask + Boto3 + MySQL 8.x application for creating, monitoring, syncing, uploading to, and deleting Amazon S3 buckets.

## Features

- Create S3 buckets with bucket type, namespace/name builder, object ownership, public access block, versioning, tags, encryption, bucket key, and object lock choices.
- Select existing AWS buckets and import/sync them into the local MySQL database.
- Monitor active and deleted buckets from a local database.
- Upload files to a selected S3 bucket.
- Sync button refreshes AWS bucket state and marks locally known missing buckets as deleted.
- Delete active S3 buckets after optionally emptying their objects and versions.
- Multipage Bootstrap UI with anime.js page animations.

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and update the values for MySQL and AWS region.

4. Create the MySQL schema if needed, then run `schema.sql` in your database:

   ```powershell
   mysql -u root -p s3_monitor < schema.sql
   ```

5. Make sure AWS credentials are configured for the logged-in user. Any normal Boto3 method works, such as:

   ```powershell
   aws configure
   ```

6. Start the app:

   ```powershell
   flask --app app run --debug
   ```

Open `http://127.0.0.1:5000`.

## Notes

- S3 bucket names are globally unique. The namespace field is prepended to the bucket name to help generate unique names.
- S3 Object Lock can only be enabled when creating a bucket and requires versioning.
- Deleting a bucket requires the bucket to be empty. This app includes an option to empty objects and versions before deleting.
- The "directory bucket / S3 Express One Zone" bucket type is shown as an option, but this implementation creates standard general-purpose S3 buckets. AWS directory buckets require different APIs and naming/location constraints.
