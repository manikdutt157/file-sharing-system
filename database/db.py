from pymongo import MongoClient
from urllib.parse import quote_plus
import os

db = None

def initialize_db(app):
    global db
    try:
        # Connect to MongoDB Atlas
        client = MongoClient(app.config['MONGODB_URI'])
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        # Use the file_share_db database
        db = client.file_share_db
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB Atlas: {e}")
        raise e

def get_db():
    global db
    if db is None:
        raise Exception("Database not initialized")
    return db 