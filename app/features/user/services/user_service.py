import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from typing import List, Optional
from app.features.user.schemas.user_schema import UserCreate, UserUpdate, LoginRequest
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

    def create_user(self, user_create: UserCreate) -> User:
        if self.user_repository.get_user_by_username(user_create.username):
            raise ValueError("Username already exists")
        hashed_password = get_password_hash(user_create.password)
        return self.user_repository.create_user(user_create.username, hashed_password, user_create.rol)

    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        update_data = {}
        if user_update.username is not None:
            existing = self.user_repository.get_user_by_username(user_update.username)
            if existing and existing.id != user_id:
                raise ValueError("Username already exists")
            update_data["username"] = user_update.username
        if user_update.password is not None:
            update_data["password"] = get_password_hash(user_update.password)
        if user_update.rol is not None:
            update_data["rol"] = user_update.rol
        return self.user_repository.update_user(user_id, **update_data)

    def delete_user(self, user_id: int) -> bool:
        if not self.user_repository.get_user_by_id(user_id):
            raise ValueError("User not found")
        return self.user_repository.delete_user(user_id)

    def login(self, login_request: LoginRequest) -> dict:
        user = self.user_repository.get_user_by_username(login_request.username)
        if not user or not verify_password(login_request.password, user.password):
            raise ValueError("Invalid credentials")
        payload = {
            "id": user.id,
            "username": user.username,
            "rol": user.rol,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm="HS256")
        return {
            "id": user.id,
            "username": user.username,
            "rol": user.rol,
            "access_token": access_token,
            "token_type": "bearer"
        }

    def follow_streamer(self, follower_id: int, streamer_id: int) -> bool:
        """Que un follower siga a un streamer"""
        # Verificar que ambos usuarios existan
        if not self.user_repository.get_user_by_id(follower_id):
            raise ValueError("Follower not found")
        if not self.user_repository.get_user_by_id(streamer_id):
            raise ValueError("Streamer not found")
        
        # Verificar que el streamer sea un streamer
        streamer = self.user_repository.get_user_by_id(streamer_id)
        if streamer.rol != 'streamer':
            raise ValueError("Can only follow streamers")
        
        # Verificar que no ya no esté siguiendo
        if self.user_repository.is_following(follower_id, streamer_id):
            raise ValueError("Already following this streamer")
        
        return self.user_repository.add_follow(follower_id, streamer_id)

    def unfollow_streamer(self, follower_id: int, streamer_id: int) -> bool:
        """Que un follower deje de seguir a un streamer"""
        if not self.user_repository.is_following(follower_id, streamer_id):
            raise ValueError("Not following this streamer")
        return self.user_repository.remove_follow(follower_id, streamer_id)

    def get_followers(self, streamer_id: int) -> List[dict]:
        """Obtener lista de followers de un streamer"""
        if not self.user_repository.get_user_by_id(streamer_id):
            raise ValueError("Streamer not found")
        return self.user_repository.get_followers(streamer_id)

    def get_following(self, follower_id: int) -> List[User]:
        """Obtener lista de streamers que sigue un usuario"""
        if not self.user_repository.get_user_by_id(follower_id):
            raise ValueError("User not found")
        return self.user_repository.get_following(follower_id)