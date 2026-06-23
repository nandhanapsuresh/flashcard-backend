from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from db import users_col
import os

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"])
SECRET = os.getenv("JWT_SECRET", "secret")


class AuthInput(BaseModel):
    email: str
    password: str


def make_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


@router.post("/signup")
def signup(data: AuthInput):
    if users_col.find_one({"email": data.email}):
        raise HTTPException(400, "Email already registered")
    hashed = pwd.hash(data.password)
    result = users_col.insert_one({
        "email": data.email,
        "password": hashed,
        "created_at": datetime.utcnow().isoformat()
    })
    token = make_token(str(result.inserted_id))
    return {"token": token}


@router.post("/login")
def login(data: AuthInput):
    user = users_col.find_one({"email": data.email})
    if not user or not pwd.verify(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    token = make_token(str(user["_id"]))
    return {"token": token}
