from time import time
from fastapi import FastAPI, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
# Secret key to encode and decode the JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 1440  # 1 day

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
app = FastAPI()
security = HTTPBasic()
app.mount("/static", StaticFiles(directory="static"), name="static")

html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI on Vercel</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon" />
    </head>
    <body>
        <div class="bg-gray-200 p-4 rounded-lg shadow-lg">
            <h1>Hello from FastAPI@{__version__}</h1>
            <ul>
                <li><a href="/docs">/docs</a></li>
                <li><a href="/redoc">/redoc</a></li>
            </ul>
            <p>Powered by <a href="https://vercel.com" target="_blank">Vercel</a></p>
        </div>
    </body>
</html>
"""

# Secret key to encode and decode the JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# OAuth2PasswordBearer is used to get the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy user database
fake_users_db = {}

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User model
class User(BaseModel):
    username: str
    full_name: str = None
    email: str = None
    disabled: bool = None

# User registration model
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = None
    email: str = None

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token:str

# Token data model
class TokenData(BaseModel):
    username: str
class RefreshToken(BaseModel):
    refresh_token: str
# Function to hash a password
def hash_password(password: str):
    return pwd_context.hash(password)

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get a user by username
def get_user(db, username: str):
    if username in db:
        return db[username]
    return None

# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to create refresh token
def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route to register a new user
@app.post("/register", response_model=User)
async def register(user: UserCreate):
    if get_user(fake_users_db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = hash_password(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    return User(username=user.username, full_name=user.full_name, email=user.email, disabled=False)

# Route to get a token
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(fake_users_db, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(data={"sub": user["username"]}, expires_delta=refresh_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

# Route to refresh access token
@app.post("/token/refresh", response_model=Token)
async def refresh_token(refresh_token: RefreshToken):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, token_data.username)
    if user is None:
        raise credentials_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Example data storage (simulated in-memory database)
fake_items_db = [
    {"item_id": "1", "name": "Item One","created_by":""},
    {"item_id": "2", "name": "Item Two","created_by":""},
]

# Define a Pydantic model for item creation
class Item(BaseModel):
    name: str
    description: str = None
    created_by:str = None
# GET endpoint to retrieve all items
@app.get("/items/")
async def read_items(current_user: User = Depends(get_current_user)):
    return fake_items_db

# GET endpoint to retrieve a specific item by ID
@app.get("/items/{item_id}")
async def read_item(item_id: str,current_user: User = Depends(get_current_user)):
    for item in fake_items_db:
        if item["item_id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# POST endpoint to create a new item
@app.post("/items/")
async def create_item(item: Item,current_user: User = Depends(get_current_user)):
    new_item = {"item_id": str(len(fake_items_db) + 1), **item.dict()}
    fake_items_db.append(new_item)
    return new_item

# PUT endpoint to update an existing item by ID
@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item,current_user: User = Depends(get_current_user)):
    for i, db_item in enumerate(fake_items_db):
        if db_item["item_id"] == item_id:
            fake_items_db[i] = {"item_id": item_id, **item.dict()}
            return {"message": "Item updated successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

# DELETE endpoint to delete an item by ID
@app.delete("/items/{item_id}")
async def delete_item(item_id: str,current_user: User = Depends(get_current_user)):
    for i, db_item in enumerate(fake_items_db):
        if db_item["item_id"] == item_id:
            del fake_items_db[i]
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

# Example of a query parameter endpoint
@app.get("/items_by_name/")
async def read_item_by_name(name: str = Query(..., min_length=3, max_length=50),current_user: User = Depends(get_current_user)):
    result = [item for item in fake_items_db if name.lower() in item["name"].lower()]
    return result


@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}


class IntroductionRequest(BaseModel):
    subtopic: str
    keywords: str
    summary: str

@app.post("/generate_introduction/")
async def generate_introduction(request: IntroductionRequest):
    introduction = f"{request.subtopic}에 대한 소개\n\n"
    introduction += f"키워드: {request.keywords}\n\n"
    introduction += f"{request.summary}"
    
    return {"introduction": introduction}


# Protected route
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
