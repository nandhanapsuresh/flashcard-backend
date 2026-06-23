from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["flashcards"]

users_col = db["users"]
sets_col = db["flashcard_sets"]