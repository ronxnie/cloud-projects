from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from . import repository
from .s3_service import S3ServiceError, create_bucket, delete_bucket, get_bucket_details, list_buckets, upload_file


bp = Blueprint("main", __name__)


OWNERSHIP_OPTIONS = [
    ("BucketOwnerEnforced", "Bucket owner enforced"),
    ("BucketOwnerPreferred", "Bucket owner preferred"),
    ("ObjectWriter", "Object writer"),
]

BUCKET_TYPE_OPTIONS = [
    ("general-purpose", "General purpose bucket"),
    ("directory", "Directory bucket / S3 Express One Zone"),
]

ENCRYPTION_OPTIONS = [
    ("AES256", "SSE-S3 (AES256)"),
    ("aws:kms", "SSE-KMS"),
]


@bp.route("/")
def dashboard():
    buckets = repository.list_local_buckets()
    uploads = repository.list_uploads()
    active_count = sum(1 for item in buckets if item["status"] == "active")
    deleted_count = sum(1 for item in buckets if item["status"] == "deleted")
    return render_template(
        "dashboard.html",
        buckets=buckets,
        uploads=uploads,
        active_count=active_count,
        deleted_count=deleted_count,
    )


@bp.route("/buckets/new", methods=["GET", "POST"])
def new_bucket():
    aws_buckets = []
    try:
        aws_buckets = list_buckets()
    except Exception as exc:
        flash(f"Unable to list existing AWS buckets: {exc}", "warning")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "import":
            bucket_name = request.form.get("existing_bucket")
            if not bucket_name:
                flash("Select an existing bucket to import.", "warning")
                return redirect(url_for("main.new_bucket"))
            return import_existing_bucket(bucket_name)

        options = parse_bucket_form(request.form)
        try:
            bucket_name = create_bucket(options)
            details = get_bucket_details(bucket_name)
            details.update(
                {
                    "bucket_type": options["bucket_type"],
                    "namespace": options.get("namespace"),
                    "metadata": {"source": "created-from-app"},
                }
            )
            repository.upsert_bucket(details)
            flash(f"Bucket {bucket_name} created successfully.", "success")
            return redirect(url_for("main.buckets"))
        except S3ServiceError as exc:
            flash(str(exc), "danger")
        except Exception as exc:
            flash(f"Unexpected error: {exc}", "danger")

    return render_template(
        "bucket_form.html",
        ownership_options=OWNERSHIP_OPTIONS,
        bucket_type_options=BUCKET_TYPE_OPTIONS,
        encryption_options=ENCRYPTION_OPTIONS,
        aws_buckets=aws_buckets,
    )


@bp.route("/buckets")
def buckets():
    return render_template("buckets.html", buckets=repository.list_local_buckets())


@bp.route("/sync", methods=["POST"])
def sync():
    try:
        aws_buckets = list_buckets()
        active_names = []
        for bucket in aws_buckets:
            details = get_bucket_details(bucket["bucket_name"])
            details["created_at"] = bucket.get("created_at")
            details["bucket_type"] = "general-purpose"
            details["metadata"] = {"source": "aws-sync"}
            repository.upsert_bucket(details)
            active_names.append(bucket["bucket_name"])
        deleted_count = repository.mark_missing_buckets_deleted(active_names)
        flash(f"Sync completed. {len(active_names)} active bucket(s), {deleted_count} marked deleted.", "success")
    except Exception as exc:
        flash(f"Sync failed: {exc}", "danger")
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/buckets/<bucket_name>/upload", methods=["GET", "POST"])
def upload(bucket_name):
    bucket = repository.get_local_bucket(bucket_name)
    if not bucket:
        flash("Bucket is not available in the local database. Run sync first.", "warning")
        return redirect(url_for("main.buckets"))

    if request.method == "POST":
        file = request.files.get("file")
        object_key = request.form.get("object_key") or None
        if not file or not file.filename:
            flash("Choose a file to upload.", "warning")
            return redirect(url_for("main.upload", bucket_name=bucket_name))
        try:
            safe_name = secure_filename(file.filename) or file.filename
            key = upload_file(bucket_name, file, object_key)
            repository.record_upload(bucket_name, key, safe_name, request.content_length or 0)
            flash(f"Uploaded {safe_name} to {bucket_name}.", "success")
            return redirect(url_for("main.upload", bucket_name=bucket_name))
        except S3ServiceError as exc:
            flash(str(exc), "danger")

    return render_template("upload.html", bucket=bucket, uploads=repository.list_uploads(bucket_name))


@bp.route("/buckets/<bucket_name>/delete", methods=["POST"])
def remove_bucket(bucket_name):
    empty_first = request.form.get("empty_first") == "on"
    try:
        deleted_at = delete_bucket(bucket_name, empty_first=empty_first)
        repository.mark_bucket_deleted(bucket_name, deleted_at.replace(tzinfo=None))
        flash(f"Bucket {bucket_name} deleted.", "success")
    except S3ServiceError as exc:
        flash(str(exc), "danger")
    except Exception as exc:
        flash(f"Delete failed: {exc}", "danger")
    return redirect(url_for("main.buckets"))


def import_existing_bucket(bucket_name):
    try:
        details = get_bucket_details(bucket_name)
        details["bucket_type"] = "general-purpose"
        details["metadata"] = {"source": "manual-import"}
        repository.upsert_bucket(details)
        flash(f"Imported {bucket_name} into the local database.", "success")
        return redirect(url_for("main.buckets"))
    except Exception as exc:
        flash(f"Import failed: {exc}", "danger")
        return redirect(url_for("main.new_bucket"))


def parse_bucket_form(form):
    tags = []
    for raw_line in form.get("tags", "").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        tags.append({"Key": key.strip(), "Value": value.strip()})

    return {
        "bucket_type": form.get("bucket_type", "general-purpose"),
        "namespace": form.get("namespace", "").strip(),
        "bucket_name": form.get("bucket_name", "").strip(),
        "region": form.get("region", "").strip(),
        "ownership": form.get("ownership"),
        "public_access_blocked": form.get("public_access_blocked") == "on",
        "versioning": form.get("versioning") == "on",
        "encryption_type": form.get("encryption_type") or "AES256",
        "kms_key_id": form.get("kms_key_id", "").strip(),
        "bucket_key_enabled": form.get("bucket_key_enabled") == "on",
        "object_lock_enabled": form.get("object_lock_enabled") == "on",
        "tags": tags,
    }
