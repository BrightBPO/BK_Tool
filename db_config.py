from peewee import MySQLDatabase
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env
load_dotenv()

# Database configuration
db_host = os.getenv("DB_HOST")
db_port = 3306
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Check if any variable is missing
missing_vars = [var for var in ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"] if os.getenv(var) is None]

if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")


# Peewee database instance
db = MySQLDatabase(None)  # Placeholder, configure it later


def initialize_database():
    """
    Ensure the database exists by connecting to MySQL without specifying the database
    and creating it if it doesn't exist.
    """
    try:
        # Connect to MySQL server without a database
        print(f"Attempting to connect to MySQL on {db_host}:{db_port}")
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"Database '{db_name}' created or already exists.")

            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error while creating database: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def configure_database():
    """
    Configure the Peewee database instance with the database name.
    """
    db.init(
        db_name,
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password
    )

# Initialize and configure the database
initialize_database()
configure_database()