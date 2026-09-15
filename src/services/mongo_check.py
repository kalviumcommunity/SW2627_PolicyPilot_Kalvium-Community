import os
from pymongo import MongoClient, errors
from dotenv import load_dotenv

load_dotenv()

def check_mongo_connection():
    uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('MONGODB_DB', 'policypilot')
    if not uri:
        print('MONGODB_URI not set in environment.')
        return False
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f'Connected to MongoDB server. Database: {db_name}')
        db = client[db_name]
        print('Collections:', db.list_collection_names())
        return True
    except errors.PyMongoError as e:
        print(f'MongoDB connection failed: {e}')
        return False

if __name__ == '__main__':
    check_mongo_connection()
