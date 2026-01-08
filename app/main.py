from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas, auth, database

app = FastAPI(title="Come On Da Sample")

@app.get("/")
async def root():
    return {"message": "Come On Da API is running", "docs": "/docs"}



@app.post("/signup", response_model=schemas.Token)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(database.get_db)):
    # Check if phone number already exists
    result = await db.execute(select(models.User).filter(models.User.phone_number == user.phone_number))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Check if email already exists
    result = await db.execute(select(models.User).filter(models.User.email == user.email))
    db_user_email = result.scalars().first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Return access token
    access_token = auth.create_access_token(data={"sub": new_user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    # Swagger UI sends 'username' and 'password' as form data
    # We map 'username' to 'phone_number'
    result = await db.execute(select(models.User).filter(models.User.phone_number == form_data.username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: AsyncSession = Depends(database.get_db)):
    # Find user by phone number
    result = await db.execute(select(models.User).filter(models.User.phone_number == user_credentials.phone_number))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Verify password
    if not auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Generate token
    access_token = auth.create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# News Endpoints
@app.post("/news", response_model=schemas.News)
async def create_news(
    news: schemas.NewsCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to perform this action"
        )
    
    new_news = models.News(**news.model_dump())
    db.add(new_news)
    await db.commit()
    await db.refresh(new_news)
    return new_news

@app.get("/news", response_model=list[schemas.News])
async def read_news(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.News).offset(skip).limit(limit).order_by(models.News.created_at.desc()))
    return result.scalars().all()

# Background Task
def log_product_creation(product_name: str):
    # Simulate a time-consuming background task
    print(f"BACKGROUND TASK: New product created - {product_name}")

# Product Endpoints
from fastapi import BackgroundTasks
from datetime import datetime, timezone

@app.post("/products", response_model=schemas.Product)
async def create_product(
    product: schemas.ProductCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to perform this action"
        )
    
    # Set default publish_at to now if not provided
    if product.publish_at is None:
        product.publish_at = datetime.now(timezone.utc)

    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # Trigger background task
    background_tasks.add_task(log_product_creation, new_product.name)

    return new_product

@app.get("/products", response_model=list[schemas.Product])
async def read_products(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db)):
    now = datetime.now(timezone.utc)
    # Only show products where publish_at <= now
    result = await db.execute(
        select(models.Product)
        .filter(models.Product.publish_at <= now)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
