from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_ops_user():
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client.file_share_db  # Changed to file_share_db

        # Check if ops user already exists
        existing_user = db.users.find_one({'email': 'ops@example.com'})
        if existing_user:
            print("\nOperations user already exists!")
            print("Current users in database:")
            users = list(db.users.find({}, {'email': 1, 'user_type': 1}))
            for user in users:
                print(f"Email: {user.get('email')}, Type: {user.get('user_type')}")
            return

        # Create password hash
        password = "ops123"  # You can change this password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create ops user
        ops_user = {
            'email': 'ops@example.com',
            'password': hashed_password,
            'user_type': 'ops',
            'verified': True
        }

        # Insert the user
        result = db.users.insert_one(ops_user)
        
        if result.inserted_id:
            print("\nOperations user created successfully!")
            print("Email: ops@example.com")
            print("Password: ops123")
            
            print("\nCurrent users in database:")
            users = list(db.users.find({}, {'email': 1, 'user_type': 1}))
            for user in users:
                print(f"Email: {user.get('email')}, Type: {user.get('user_type')}")
        else:
            print("Failed to create operations user.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()

def clear_users():
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client.file_share_db

        # Delete all users
        result = db.users.delete_many({})
        print(f"\nDeleted {result.deleted_count} users")
        print("Database cleared successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    choice = input("Do you want to clear existing users first? (yes/no): ")
    if choice.lower() == 'yes':
        clear_users()
    create_ops_user() 