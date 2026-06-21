from datetime import datetime, timezone
import re

import boto3
from botocore.exceptions import ClientError
from flask import current_app


BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


class S3ServiceError(RuntimeError):
    pass


def s3_client():
    return boto3.client("s3", region_name=current_app.config["AWS_REGION"])


def normalize_bucket_name(namespace, bucket_name):
    parts = [part.strip().lower() for part in (namespace, bucket_name) if part and part.strip()]
    full_name = "-".join(parts)
    full_name = re.sub(r"[^a-z0-9.-]+", "-", full_name)
    full_name = re.sub(r"-{2,}", "-", full_name).strip("-.")
    if not BUCKET_NAME_RE.match(full_name) or ".." in full_name or ".-" in full_name or "-." in full_name:
        raise S3ServiceError(
            "Bucket name must be 3-63 characters, lowercase, and contain only letters, numbers, dots, or hyphens."
        )
    return full_name


def list_buckets():
    client = s3_client()
    response = client.list_buckets()
    buckets = []
    for bucket in response.get("Buckets", []):
        name = bucket["Name"]
        buckets.append(
            {
                "bucket_name": name,
                "created_at": bucket.get("CreationDate"),
                "region": get_bucket_region(client, name),
            }
        )
    return buckets


def get_bucket_region(client, bucket_name):
    try:
        response = client.get_bucket_location(Bucket=bucket_name)
        return response.get("LocationConstraint") or "us-east-1"
    except ClientError:
        return None


def get_bucket_details(bucket_name):
    client = s3_client()
    details = {
        "bucket_name": bucket_name,
        "region": get_bucket_region(client, bucket_name),
        "ownership": None,
        "public_access_blocked": None,
        "versioning": "Suspended",
        "encryption_type": None,
        "bucket_key_enabled": False,
        "object_lock_enabled": False,
        "tags": [],
    }

    try:
        ownership = client.get_bucket_ownership_controls(Bucket=bucket_name)
        rules = ownership.get("OwnershipControls", {}).get("Rules", [])
        if rules:
            details["ownership"] = rules[0].get("ObjectOwnership")
    except ClientError:
        pass

    try:
        pab = client.get_public_access_block(Bucket=bucket_name)
        config = pab.get("PublicAccessBlockConfiguration", {})
        details["public_access_blocked"] = all(
            config.get(key, False)
            for key in (
                "BlockPublicAcls",
                "IgnorePublicAcls",
                "BlockPublicPolicy",
                "RestrictPublicBuckets",
            )
        )
    except ClientError:
        details["public_access_blocked"] = False

    try:
        versioning = client.get_bucket_versioning(Bucket=bucket_name)
        details["versioning"] = versioning.get("Status", "Suspended")
        details["object_lock_enabled"] = versioning.get("MFADelete") == "Enabled"
    except ClientError:
        pass

    try:
        encryption = client.get_bucket_encryption(Bucket=bucket_name)
        rule = encryption["ServerSideEncryptionConfiguration"]["Rules"][0]
        default = rule.get("ApplyServerSideEncryptionByDefault", {})
        details["encryption_type"] = default.get("SSEAlgorithm")
        details["bucket_key_enabled"] = rule.get("BucketKeyEnabled", False)
    except ClientError:
        pass

    try:
        tags = client.get_bucket_tagging(Bucket=bucket_name)
        details["tags"] = tags.get("TagSet", [])
    except ClientError:
        pass

    try:
        lock = client.get_object_lock_configuration(Bucket=bucket_name)
        details["object_lock_enabled"] = bool(lock.get("ObjectLockConfiguration"))
    except ClientError:
        pass

    return details


def create_bucket(options):
    client = s3_client()
    if options.get("bucket_type") == "directory":
        raise S3ServiceError(
            "Directory buckets / S3 Express One Zone need the S3 Control APIs and additional location constraints. "
            "Choose a general purpose bucket in this app."
        )
    bucket_name = normalize_bucket_name(options.get("namespace"), options["bucket_name"])
    region = options.get("region") or current_app.config["AWS_REGION"]
    params = {"Bucket": bucket_name}

    if region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    if options.get("object_lock_enabled"):
        params["ObjectLockEnabledForBucket"] = True

    try:
        client.create_bucket(**params)
        waiter = client.get_waiter("bucket_exists")
        waiter.wait(Bucket=bucket_name)
        apply_bucket_configuration(client, bucket_name, options)
        return bucket_name
    except ClientError as exc:
        raise S3ServiceError(exc.response.get("Error", {}).get("Message", str(exc))) from exc


def apply_bucket_configuration(client, bucket_name, options):
    ownership = options.get("ownership")
    if ownership:
        client.put_bucket_ownership_controls(
            Bucket=bucket_name,
            OwnershipControls={"Rules": [{"ObjectOwnership": ownership}]},
        )

    if options.get("public_access_blocked"):
        client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
    else:
        try:
            client.delete_public_access_block(Bucket=bucket_name)
        except ClientError:
            pass

    versioning_status = "Enabled" if options.get("versioning") or options.get("object_lock_enabled") else "Suspended"
    client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": versioning_status})

    encryption_type = options.get("encryption_type")
    if encryption_type:
        default_encryption = {"SSEAlgorithm": encryption_type}
        if encryption_type == "aws:kms" and options.get("kms_key_id"):
            default_encryption["KMSMasterKeyID"] = options["kms_key_id"]
        client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": default_encryption,
                        "BucketKeyEnabled": bool(options.get("bucket_key_enabled")),
                    }
                ]
            },
        )

    tags = options.get("tags") or []
    if tags:
        client.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": tags})


def upload_file(bucket_name, file_storage, object_key=None):
    client = s3_client()
    key = object_key or file_storage.filename
    try:
        client.upload_fileobj(file_storage.stream, bucket_name, key)
        return key
    except ClientError as exc:
        raise S3ServiceError(exc.response.get("Error", {}).get("Message", str(exc))) from exc


def delete_bucket(bucket_name, empty_first=False):
    client = s3_client()
    try:
        if empty_first:
            empty_bucket(client, bucket_name)
        client.delete_bucket(Bucket=bucket_name)
        return datetime.now(timezone.utc)
    except ClientError as exc:
        raise S3ServiceError(exc.response.get("Error", {}).get("Message", str(exc))) from exc


def empty_bucket(client, bucket_name):
    paginator = client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name):
        objects = []
        for version in page.get("Versions", []):
            objects.append({"Key": version["Key"], "VersionId": version["VersionId"]})
        for marker in page.get("DeleteMarkers", []):
            objects.append({"Key": marker["Key"], "VersionId": marker["VersionId"]})
        if objects:
            client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects, "Quiet": True})

    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        objects = [{"Key": item["Key"]} for item in page.get("Contents", [])]
        if objects:
            client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects, "Quiet": True})
