# Monitor EC2 Instance

A Flask + Boto3 project to create, monitor, start, stop, terminate, and locally sync AWS EC2 instances into a MySQL 8.x database.

## Features

- Create EC2 instances from a multipage Bootstrap UI.
- Select an operating system from a curated list. The app resolves the latest matching AMI in your configured AWS region.
- Select an EC2 instance type. The app loads current AWS instance types when AWS credentials are available, with fallback common options.
- List running, stopped, pending, stopping, shutting-down, and terminated instances.
- Start, stop, terminate, delete local terminated records, and sync AWS EC2 state into MySQL.
- Uses anime.js for small UI transitions and Bootstrap CSS for layout.

## Setup

1. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and update your AWS region and MySQL credentials.

   ```powershell
   Copy-Item .env.example .env
   ```

4. Make sure your AWS credentials are configured using one of the standard Boto3 methods:

   ```powershell
   aws configure
   ```

5. Initialize the MySQL table.

   ```powershell
   python init_db.py
   ```

6. Run the Flask app.

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.

## IAM Permissions

Use an IAM user or role with EC2 permissions for:

- `ec2:DescribeImages`
- `ec2:DescribeInstanceTypes`
- `ec2:DescribeInstances`
- `ec2:RunInstances`
- `ec2:StartInstances`
- `ec2:StopInstances`
- `ec2:TerminateInstances`

## Database

The app expects the database named in `.env` to already exist. `init_db.py` creates the required `ec2_instances` table.

## Notes

- Terminating an EC2 instance deletes it from AWS after shutdown completes. The app keeps the local record until you delete the local terminated record or sync again.
- You are responsible for AWS costs. Check selected instance type, region, storage, and key pair before launching.
