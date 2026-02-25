from fastapi import APIRouter, HTTPException
from typing import List
from app.features.user.schemas.user_schema import UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse
from app.features.user.services.user_service import UserService

router = APIRouter()

@router.get("/users/", response_model=List[UserResponse])
def get_all_users():
    return UserService().get_all_users()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    try:
        return UserService().get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/users/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    try:
        return UserService().create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate):
    try:
        return UserService().update_user(user_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    try:
        UserService().delete_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/users/username/{username}", response_model=UserResponse)
def get_user_by_username(username: str):
    user = UserService().get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    try:
        result = UserService().login(credentials)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/follow/{follower_id}/{streamer_id}", status_code=201)
def follow_streamer(follower_id: int, streamer_id: int):
    """Un follower sigue a un streamer"""
    try:
        UserService().follow_streamer(follower_id, streamer_id)
        return {"message": f"User {follower_id} now follows streamer {streamer_id}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/follow/{follower_id}/{streamer_id}", status_code=200)
def unfollow_streamer(follower_id: int, streamer_id: int):
    """Un follower deja de seguir a un streamer"""
    try:
        UserService().unfollow_streamer(follower_id, streamer_id)
        return {"message": f"User {follower_id} unfollowed streamer {streamer_id}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/streamers/{streamer_id}/followers")
def get_streamer_followers(streamer_id: int):
    """Obtener lista de followers de un streamer"""
    try:
        followers = UserService().get_followers(streamer_id)
        return {"streamer_id": streamer_id, "followers": followers}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/users/{user_id}/following", response_model=List[UserResponse])
def get_user_following(user_id: int):
    """Obtener lista de streamers que sigue un usuario"""
    try:
        return UserService().get_following(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        return {
            "id": result["user"].id,
            "username": result["user"].username,
            "access_token": result["access_token"],
            "token_type": result["token_type"]
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))