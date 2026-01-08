from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    phone_number: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: str | None = None

class NewsBase(BaseModel):
    title: str
    content: str
    image_url: str | None = None

class NewsCreate(NewsBase):
    pass

class News(NewsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    image_url: str | None = None
    publish_at: datetime | None = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    publish_at: datetime

    class Config:
        from_attributes = True
