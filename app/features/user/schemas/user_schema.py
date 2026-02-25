from pydantic import BaseModel, ConfigDict, EmailStr

class UserBase(BaseModel):
    username: str | None = "user"
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str | None = "1"

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int

class LoginResponse(UserResponse):
    access_token: str
    token_type: str