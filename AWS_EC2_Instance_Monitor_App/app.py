from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from flask import Flask, flash, redirect, render_template, request, url_for

from aws_ec2 import (
    get_instance_types,
    get_os_catalog,
    launch_instance,
    list_instances_from_aws,
    start_instance,
    stop_instance,
    terminate_instance,
)
from config import Config
from db import delete_local_instance, get_instances, init_db, update_instance_state, upsert_instance


app = Flask(__name__)
app.config.from_object(Config)


def friendly_error(error):
    if isinstance(error, NoCredentialsError):
        return "AWS credentials were not found. Run aws configure or set AWS credentials in your environment."
    return str(error)


@app.before_request
def ensure_database():
    if not getattr(app, "_db_ready", False):
        init_db()
        app._db_ready = True


@app.route("/")
def dashboard():
    try:
        instances = get_instances()
    except Exception as error:
        instances = []
        flash(f"Database error: {friendly_error(error)}", "danger")
    return render_template("dashboard.html", instances=instances, region=Config.AWS_REGION)


@app.route("/create", methods=["GET", "POST"])
def create_instance():
    if request.method == "POST":
        try:
            created_instances = launch_instance(request.form)
            for instance in created_instances:
                upsert_instance(instance)
            flash(f"Created {len(created_instances)} EC2 instance(s).", "success")
            return redirect(url_for("dashboard"))
        except (BotoCoreError, ClientError, ValueError, RuntimeError, Exception) as error:
            flash(f"Unable to create instance: {friendly_error(error)}", "danger")

    return render_template(
        "create.html",
        operating_systems=get_os_catalog(),
        instance_types=get_instance_types(),
        region=Config.AWS_REGION,
    )


@app.route("/sync", methods=["POST"])
def sync_instances():
    try:
        instances = list_instances_from_aws()
        for instance in instances:
            upsert_instance(instance)
        flash(f"Synced {len(instances)} EC2 instance(s) from AWS.", "success")
    except (BotoCoreError, ClientError, Exception) as error:
        flash(f"Sync failed: {friendly_error(error)}", "danger")
    return redirect(url_for("dashboard"))


@app.route("/instances/<instance_id>/start", methods=["POST"])
def start(instance_id):
    try:
        start_instance(instance_id)
        update_instance_state(instance_id, "pending")
        flash(f"Start requested for {instance_id}.", "success")
    except (BotoCoreError, ClientError, Exception) as error:
        flash(f"Unable to start {instance_id}: {friendly_error(error)}", "danger")
    return redirect(url_for("dashboard"))


@app.route("/instances/<instance_id>/stop", methods=["POST"])
def stop(instance_id):
    try:
        stop_instance(instance_id)
        update_instance_state(instance_id, "stopping")
        flash(f"Stop requested for {instance_id}.", "success")
    except (BotoCoreError, ClientError, Exception) as error:
        flash(f"Unable to stop {instance_id}: {friendly_error(error)}", "danger")
    return redirect(url_for("dashboard"))


@app.route("/instances/<instance_id>/terminate", methods=["POST"])
def terminate(instance_id):
    try:
        terminate_instance(instance_id)
        update_instance_state(instance_id, "shutting-down")
        flash(f"Terminate requested for {instance_id}.", "warning")
    except (BotoCoreError, ClientError, Exception) as error:
        flash(f"Unable to terminate {instance_id}: {friendly_error(error)}", "danger")
    return redirect(url_for("dashboard"))


@app.route("/instances/<instance_id>/delete-local", methods=["POST"])
def delete_local(instance_id):
    try:
        delete_local_instance(instance_id)
        flash(f"Deleted local record for {instance_id}.", "success")
    except Exception as error:
        flash(f"Unable to delete local record: {friendly_error(error)}", "danger")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
