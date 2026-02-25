import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from typing import List, Optional
from app.features.user.models.user import User
from app.features.user.repositories.user_repository import UserRepository
from app.shared.config.middleware.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()

    def get_all_users(self) -> List[User]:
        return self.user_repository.get_all_users()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.user_repository.get_user_by_username(username)

    def create_user(self, username: str, password: str) -> User:
        if self.user_repository.get_user_by_username(username):
            raise ValueError("Username already exists")
        hashed_password = get_password_hash(password)
        return self.user_repository.create_user(username, hashed_password)

    def update_user(self, user_id: int, username: str = None, password: str = None) -> User:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        update_data = {}
        if username is not None:
            existing = self.user_repository.get_user_by_username(username)
            if existing and existing.id != user_id:
                raise ValueError("Username already exists")
            update_data["username"] = username
        if password is not None:
            update_data["password"] = get_password_hash(password)
        return self.user_repository.update_user(user_id, **update_data)

    def delete_user(self, user_id: int) -> bool:
        if not self.user_repository.get_user_by_id(user_id):
            raise ValueError("User not found")
        return self.user_repository.delete_user(user_id)

    def login(self, username: str, password: str) -> dict:
        user = self.user_repository.get_user_by_username(username)
        if not user or not verify_password(password, user.password):
            raise ValueError("Invalid credentials")
        payload = {
            "id": user.id,
            "username": user.username,
        }
        token = create_access_token(payload)
        return {"user": user, "access_token": token, "token_type": "bearer"}