from contextlib import contextmanager

import mysql.connector

from config import Config


TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ec2_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(255) NULL,
    instance_type VARCHAR(64) NULL,
    image_id VARCHAR(32) NULL,
    os_name VARCHAR(255) NULL,
    state VARCHAR(32) NOT NULL,
    public_ip VARCHAR(64) NULL,
    private_ip VARCHAR(64) NULL,
    availability_zone VARCHAR(64) NULL,
    launch_time DATETIME NULL,
    synced_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


@contextmanager
def get_connection():
    connection = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
    )
    try:
        yield connection
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(TABLE_SQL)
        connection.commit()
        cursor.close()


def upsert_instance(instance):
    sql = """
    INSERT INTO ec2_instances (
        instance_id, name, instance_type, image_id, os_name, state,
        public_ip, private_ip, availability_zone, launch_time
    ) VALUES (
        %(instance_id)s, %(name)s, %(instance_type)s, %(image_id)s, %(os_name)s, %(state)s,
        %(public_ip)s, %(private_ip)s, %(availability_zone)s, %(launch_time)s
    )
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        instance_type = VALUES(instance_type),
        image_id = VALUES(image_id),
        os_name = VALUES(os_name),
        state = VALUES(state),
        public_ip = VALUES(public_ip),
        private_ip = VALUES(private_ip),
        availability_zone = VALUES(availability_zone),
        launch_time = VALUES(launch_time),
        synced_at = CURRENT_TIMESTAMP
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, instance)
        connection.commit()
        cursor.close()


def get_instances():
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM ec2_instances
            ORDER BY
                CASE state
                    WHEN 'running' THEN 1
                    WHEN 'pending' THEN 2
                    WHEN 'stopped' THEN 3
                    WHEN 'stopping' THEN 4
                    ELSE 5
                END,
                COALESCE(launch_time, created_at) DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows


def update_instance_state(instance_id, state):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE ec2_instances SET state = %s, synced_at = CURRENT_TIMESTAMP WHERE instance_id = %s",
            (state, instance_id),
        )
        connection.commit()
        cursor.close()


def delete_local_instance(instance_id):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ec2_instances WHERE instance_id = %s", (instance_id,))
        connection.commit()
        cursor.close()
