CREATE TABLE IF NOT EXISTS s3_buckets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bucket_name VARCHAR(63) NOT NULL UNIQUE,
    bucket_type VARCHAR(40) NOT NULL DEFAULT 'general-purpose',
    namespace VARCHAR(120) NULL,
    region VARCHAR(64) NULL,
    ownership VARCHAR(64) NULL,
    public_access_blocked BOOLEAN NOT NULL DEFAULT TRUE,
    versioning VARCHAR(32) NULL,
    encryption_type VARCHAR(64) NULL,
    bucket_key_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    object_lock_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    status ENUM('active', 'deleted') NOT NULL DEFAULT 'active',
    created_at DATETIME NULL,
    deleted_at DATETIME NULL,
    last_synced_at DATETIME NOT NULL,
    tags_json JSON NULL,
    metadata_json JSON NULL,
    INDEX idx_s3_buckets_status (status),
    INDEX idx_s3_buckets_last_synced_at (last_synced_at)
);

CREATE TABLE IF NOT EXISTS s3_uploads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bucket_name VARCHAR(63) NOT NULL,
    object_key VARCHAR(1024) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    uploaded_at DATETIME NOT NULL,
    INDEX idx_s3_uploads_bucket_name (bucket_name)
);
