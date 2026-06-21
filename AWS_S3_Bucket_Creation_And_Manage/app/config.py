import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "s3_monitor")
    MAX_CONTENT_LENGTH = 250 * 1024 * 1024
