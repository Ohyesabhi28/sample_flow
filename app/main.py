from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas, auth, database, crud, email_util
from dotenv import load_dotenv

load_dotenv()

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_product_creation(product_name: str):
    logging.info(f"New product created: {product_name}")




app = FastAPI(title="Come On Da Sample")

@app.get("/")
async def root():
    return {"message": "Come On Da API is running", "docs": "/docs"}



@app.post("/signup", response_model=schemas.Token)
async def signup(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(database.get_db)):
    # Check if phone number already exists
    db_user = await crud.get_user_by_phone(db, user.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Check if email already exists
    db_user_email = await crud.get_user_by_email(db, user.email)
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

    # Trigger background task for welcome email
    background_tasks.add_task(email_util.send_welcome_email, new_user.email, new_user.username)

    # Return access token
    access_token = auth.create_access_token(data={"sub": new_user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    # Swagger UI sends 'username' and 'password' as form data
    # We map 'username' to 'phone_number'
    user = await crud.get_user_by_phone(db, form_data.username)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: AsyncSession = Depends(database.get_db)):
    # Find user by phone number
    user = await crud.get_user_by_phone(db, user_credentials.phone_number)

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

@app.post("/users/me/profile", response_model=schemas.UserProfile)
async def create_update_profile(
    profile: schemas.UserProfileCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.profile:
        for key, value in profile.model_dump(exclude_unset=True).items():
            setattr(current_user.profile, key, value)
        db.add(current_user.profile)
        await db.commit()
        await db.refresh(current_user.profile)
        return current_user.profile
    else:
        new_profile = models.UserProfile(**profile.model_dump(), user_id=current_user.id)
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile

@app.get("/users", response_model=list[schemas.User])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = await db.execute(select(models.User).options(selectinload(models.User.profile)).offset(skip).limit(limit))
    return result.scalars().all()

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
    new_news = await crud.create_news(db, new_news)
    return new_news

@app.get("/news", response_model=list[schemas.News])
async def read_news(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db)):
    return await crud.get_news(db, skip=skip, limit=limit)



# Product Endpoints

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
    new_product = await crud.create_product(db, new_product)

    # Trigger background task
    background_tasks.add_task(log_product_creation, new_product.name)

    return new_product

@app.get("/products", response_model=list[schemas.Product])
async def read_products(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db)):
    now = datetime.now(timezone.utc)
    # Only show products where publish_at <= now
    return await crud.get_active_products(db, now, skip=skip, limit=limit)

# Question Endpoints
@app.post("/questions", response_model=schemas.Question)
async def create_question(
    question: schemas.QuestionCreate, 
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to perform this action"
        )
    
    new_question = models.Question(**question.model_dump())
    new_question = await crud.create_question(db, new_question)
    return new_question

@app.get("/questions", response_model=list[schemas.QuestionPublic])
async def read_questions(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):

    # Assuming questions are visible to all authenticated users
    return await crud.get_questions(db, skip=skip, limit=limit)

@app.post("/questions/{question_id}/check", response_model=schemas.AnswerResult)
async def check_answer(
    question_id: int,
    answer_check: schemas.AnswerCheck,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    question = await crud.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = question.answer.strip().lower() == answer_check.answer.strip().lower()
    
    if is_correct:
        # Prize distribution logic
        if not current_user.profile:
            # Create profile if it doesn't exist
            new_profile = models.UserProfile(user_id=current_user.id, wins=0, losses=0, total_cash=0.0)
            db.add(new_profile)
            await db.commit()
            # Reload user to get the new profile
            await db.refresh(current_user, attribute_names=["profile"])
        
        # Award prize
        current_user.profile.wins += 1
        current_user.profile.total_cash += 10.0
        
        db.add(current_user.profile)
        await db.commit()
        await db.refresh(current_user.profile)

        return {"correct": True, "message": "Correct answer! You won $10.00!"}
    else:
        # Optional: Increment losses
        if not current_user.profile:
             new_profile = models.UserProfile(user_id=current_user.id, wins=0, losses=0, total_cash=0.0)
             db.add(new_profile)
             await db.commit()
             await db.refresh(current_user, attribute_names=["profile"])
             
        current_user.profile.losses += 1
        db.add(current_user.profile)
        await db.commit()
        
        return {"correct": False, "message": "Incorrect answer. Try again."}
