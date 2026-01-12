from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    password: str

class UserProfileBase(BaseModel):
    address: str | None = None
    wins: int = 0
    losses: int = 0
    total_cash: float = 0.0
    mage: str | None = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    is_admin: bool = False
    profile: UserProfile | None = None
    
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

class QuestionBase(BaseModel):
    text: str
    answer: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
