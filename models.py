"""Application Models"""
from turtle import update
import bson
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

DATABASE_URL = os.environ.get(
    'DATABASE_URL') or 'mongodb://localhost:27017/myDatabase'
print(DATABASE_URL)
client = MongoClient(DATABASE_URL)
db = client.myDatabase


class User:
    """User Model"""

    def __init__(self):
        return

    def create(self, username="", email="", password=""):
        """Create a new user"""
        user = self.get_by_email(email)
        if user:
            return
        new_user = db.users.insert_one(
            {
                "username": username,
                "email": email,
                "password": self.encrypt_password(password),
                "bio": "",
                "image": "https://api.realworld.io/images/smiley-cyrus.jpeg"
            }
        )
        Nonce().create(email)
        return self.get_by_id(new_user.inserted_id)

    def get_all(self):
        """Get all users"""
        users = db.users.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, user_id):
        """Get a user by id"""
        user = db.users.find_one(
            {"_id": bson.ObjectId(user_id)})
        if not user:
            return
        user["_id"] = str(user["_id"])
        user.pop("password")
        return user

    def get_by_email(self, email):
        """Get a user by email"""
        user = db.users.find_one({"email": email})
        if not user:
            return
        user["_id"] = str(user["_id"])
        return user

    def update(self, user, curr_email):
        """Update a user"""

        data = {}
        current_user = self.get_by_email(curr_email)
        if user.get("email"):
            data["email"] = user.get("email")
        if user.get("username"):
            data["username"] = user.get("username")
        if user.get("password"):
            data["password"] = user.get("password")
        if user.get("bio"):
            data["bio"] = user.get("bio")
        if user.get("image"):
            data["image"] = user.get("image")

        db.users.update_one(
            {"email": curr_email},
            {
                "$set": data
            }
        )
        updated_user = self.get_by_email(user.get("email"))
        updated_user.pop("_id")
        updated_user.pop("password")
        return updated_user

    def delete(self, user_id):
        """Delete a user"""
        Books().delete_by_user_id(user_id)
        user = db.users.delete_one({"_id": bson.ObjectId(user_id)})
        user = self.get_by_id(user_id)
        return user

    def disable_account(self, user_id):
        """Disable a user account"""
        user = db.users.update_one(
            {"_id": bson.ObjectId(user_id)},
            {"$set": {"active": False}}
        )
        user = self.get_by_id(user_id)
        return user

    def encrypt_password(self, password):
        """Encrypt password"""
        return generate_password_hash(password)

    def login(self, email, password):
        """Login a user"""

        user = self.get_by_email(email)

        if not user or not check_password_hash(user["password"], password):
            return

        user.pop("password")
        Nonce().update(email)

        return user

    def logoff(self, email):
        """Logoff a user"""
        Nonce().update(email)

# Article **********************************************************************


class Article:
    """Article Model"""

    def __init__(self):
        return

    def create(self, slug="", title="", description="", body="", tags=[], author="", favorited="", favorites_count=""):
        """Create a new Article"""
        article = self.get_by_slug(slug)
        if article:
            return
        new_article = db.article.insert_one(
            {
                "slug": slug,
                "title": title,
                "description": description,
                "body": body,
                "tags": tags,
                "author": author,
                "favorited": favorited,
                "favorites_count": favorites_count
            }
        )
        return self.get_by_id(new_article.inserted_id)

    def get_by_slug(self, slug):
        """Get a article by slug"""
        article = db.article.find_one({"slug": slug})
        if not article:
            return
        # article["slug"] = str(article["slug"])
        return article

    def get_by_id(self, article_id):
        """Get a user by id"""
        article = db.article.find_one(
            {"_id": bson.ObjectId(article_id)})
        if not article:
            return
        article["_id"] = str(article["_id"])
        return article

# Nonce **********************************************************************


class Nonce:
    """Nonce Model"""

    def __init__(self):
        return

    def create(self, email):
        """Create a new nonce"""
        reset_nonce = db.nonce.insert_one(
            {
                "nonce": 1,
                "user": email
            }
        )

    def update(self, email):
        """Update a user"""

        db.nonce.update(
            {"user": email}, {"$inc": {"nonce": 1}}
        )
        # db.nonce.find_and_modify({
        #     "query": {"nonce": {"$gt": 0}},
        #     "update": {"$inc": {"nonce": 1}},
        # })

    def reset(self, email):
        """Reset Nonce"""

        db.nonce.update(
            {"user": email}, {"nonce": 1}
        )

    def curr_nonce(self, email):
        """Current Nonce value"""

        curr_nonce = db.nonce.find_one({"user": email})

        return curr_nonce["nonce"]
