import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, UTC

from db.database import get_db
# FIX: Import models directly from their files, not through the __init__.py
from models.user import User as UserModel
from schemas import user as user_schema
from schemas import token as token_schema
from core.config import settings

# --- Password Hashing & Token utils ---
from passlib.context import CryptContext
from jose import JWTError, jwt

# Using argon2 is a great choice, as you noted.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
# --- End of Utils ---


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=user_schema.User)
def register_user(
    user: user_schema.UserCreate, # <-- This schema now contains all the new fields
    db: Session = Depends(get_db)
):
    # Check if email already exists
    db_user_email = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user_username = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    hashed_password = get_password_hash(user.password)
    
    # Create the new user object with all fields from the schema
    new_user = UserModel(
        email=user.email,
        hashed_password=hashed_password,
        username=user.username,
        gender=user.gender,
        date_of_birth=user.date_of_birth,
        school=user.school,
        major=user.major
    )
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/token", response_model=token_schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Note: Login still uses email (form_data.username)
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- Auth Dependency (No changes needed here) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = token_schema.TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(UserModel).filter(UserModel.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user