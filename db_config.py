from peewee import MySQLDatabase
import mysql.connector
from mysql.connector import Error
import os

# Database configuration
db_host = "localhost"  # Use ENV variable, default to localhost
db_port = 3306
db_user = "admin"
db_password = "Admin@123"
db_name = "pacer_bankruptcy"

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