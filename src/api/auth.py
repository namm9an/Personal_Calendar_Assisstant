from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import os

from ..core.config import settings
from ..models.mongodb_models import User, MongoBaseModel
from ..db.connection import mongodb
from ..core.exceptions import AuthenticationError
from ..utils.token_encryption import TokenEncryption

router = APIRouter()

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# JWT Constants
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime

class TokenData(BaseModel):
    user_id: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    timezone: str = "UTC"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    timezone: str

# Helper functions
def verify_password(plain_password, hashed_password):
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]):
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    user = await mongodb.db.users.find_one({"email": email})
    return user

async def authenticate_user(email: str, password: str):
    """Authenticate a user with email and password."""
    user = await get_user_by_email(email)
    
    if not user:
        return False
    
    if not verify_password(password, user.get("password")):
        return False
    
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = await mongodb.db.users.find_one({"_id": token_data.user_id})
    
    if user is None:
        raise credentials_exception
    
    return user

# Routes
@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate, response: Response):
    """Create a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        timezone=user_data.timezone
    )
    
    # Add the password field (not part of the User model)
    user_dict = new_user.model_dump()
    user_dict["password"] = hashed_password
    
    # Insert into database
    result = await mongodb.db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Set cookies
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        expires=(datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires,
    )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    """Login and get access token."""
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = str(user["_id"])
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Set cookies if response is provided
    if response:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="lax",
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="lax",
            expires=(datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token."""
    # Try to get the refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    # If not in cookie, try to get from Authorization header
    if not refresh_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate new tokens
        new_access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        # Update cookies
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="lax",
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="lax",
            expires=(datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_at=expires,
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user.get("name"),
        timezone=current_user.get("timezone", "UTC"),
    )

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"} 