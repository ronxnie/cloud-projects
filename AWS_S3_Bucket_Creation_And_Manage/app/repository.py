from datetime import datetime, timezone

from .db import db_cursor, dumps_json


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upsert_bucket(bucket):
    now = utc_now()
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO s3_buckets (
                bucket_name, bucket_type, namespace, region, ownership,
                public_access_blocked, versioning, encryption_type,
                bucket_key_enabled, object_lock_enabled, status, created_at,
                deleted_at, last_synced_at, tags_json, metadata_json
            )
            VALUES (
                %(bucket_name)s, %(bucket_type)s, %(namespace)s, %(region)s, %(ownership)s,
                %(public_access_blocked)s, %(versioning)s, %(encryption_type)s,
                %(bucket_key_enabled)s, %(object_lock_enabled)s, 'active', %(created_at)s,
                NULL, %(last_synced_at)s, %(tags_json)s, %(metadata_json)s
            )
            ON DUPLICATE KEY UPDATE
                bucket_type = VALUES(bucket_type),
                namespace = COALESCE(VALUES(namespace), namespace),
                region = VALUES(region),
                ownership = VALUES(ownership),
                public_access_blocked = VALUES(public_access_blocked),
                versioning = VALUES(versioning),
                encryption_type = VALUES(encryption_type),
                bucket_key_enabled = VALUES(bucket_key_enabled),
                object_lock_enabled = VALUES(object_lock_enabled),
                status = 'active',
                deleted_at = NULL,
                last_synced_at = VALUES(last_synced_at),
                tags_json = VALUES(tags_json),
                metadata_json = VALUES(metadata_json)
            """,
            {
                "bucket_name": bucket["bucket_name"],
                "bucket_type": bucket.get("bucket_type", "general-purpose"),
                "namespace": bucket.get("namespace"),
                "region": bucket.get("region"),
                "ownership": bucket.get("ownership"),
                "public_access_blocked": bool(bucket.get("public_access_blocked", True)),
                "versioning": bucket.get("versioning"),
                "encryption_type": bucket.get("encryption_type"),
                "bucket_key_enabled": bool(bucket.get("bucket_key_enabled", False)),
                "object_lock_enabled": bool(bucket.get("object_lock_enabled", False)),
                "created_at": bucket.get("created_at"),
                "last_synced_at": now,
                "tags_json": dumps_json(bucket.get("tags", [])),
                "metadata_json": dumps_json(bucket.get("metadata", {})),
            },
        )


def list_local_buckets(status=None):
    query = "SELECT * FROM s3_buckets"
    params = ()
    if status:
        query += " WHERE status = %s"
        params = (status,)
    query += " ORDER BY status ASC, bucket_name ASC"
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def get_local_bucket(bucket_name):
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM s3_buckets WHERE bucket_name = %s", (bucket_name,))
        return cursor.fetchone()


def mark_missing_buckets_deleted(active_names):
    now = utc_now()
    with db_cursor() as cursor:
        if active_names:
            placeholders = ", ".join(["%s"] * len(active_names))
            cursor.execute(
                f"""
                UPDATE s3_buckets
                SET status = 'deleted', deleted_at = COALESCE(deleted_at, %s), last_synced_at = %s
                WHERE status = 'active' AND bucket_name NOT IN ({placeholders})
                """,
                (now, now, *active_names),
            )
        else:
            cursor.execute(
                """
                UPDATE s3_buckets
                SET status = 'deleted', deleted_at = COALESCE(deleted_at, %s), last_synced_at = %s
                WHERE status = 'active'
                """,
                (now, now),
            )
        return cursor.rowcount


def mark_bucket_deleted(bucket_name, deleted_at=None):
    now = utc_now()
    with db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE s3_buckets
            SET status = 'deleted', deleted_at = %s, last_synced_at = %s
            WHERE bucket_name = %s
            """,
            (deleted_at or now, now, bucket_name),
        )


def record_upload(bucket_name, object_key, file_name, size_bytes):
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO s3_uploads (bucket_name, object_key, file_name, size_bytes, uploaded_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (bucket_name, object_key, file_name, size_bytes, utc_now()),
        )


def list_uploads(bucket_name=None):
    query = "SELECT * FROM s3_uploads"
    params = ()
    if bucket_name:
        query += " WHERE bucket_name = %s"
        params = (bucket_name,)
    query += " ORDER BY uploaded_at DESC LIMIT 50"
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()
