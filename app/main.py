from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas, auth, database

app = FastAPI(title="Come On Da Sample")

@app.on_event("startup")
async def startup():
    async with database.engine.begin() as conn:
        # Create tables (useful for development, but ideally use Alembic)
        # await conn.run_sync(models.Base.metadata.create_all) 
        pass

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
