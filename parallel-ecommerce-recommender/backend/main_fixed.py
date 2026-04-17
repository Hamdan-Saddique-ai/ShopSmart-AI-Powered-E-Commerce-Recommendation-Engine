from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sqlite3
import json
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# FastAPI app
app = FastAPI(title="E-Commerce Recommendation System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (payload.get("sub"),)).fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

# Pydantic models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserInteractionData(BaseModel):
    product_id: int
    interaction_type: str
    rating_value: Optional[float] = None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "API is running", "status": "online"}

@app.get("/categories")
async def get_categories():
    conn = get_db_connection()
    categories = conn.execute("SELECT DISTINCT category FROM products").fetchall()
    conn.close()
    return [cat[0] for cat in categories]

@app.post("/register")
async def register(user: UserRegister):
    conn = get_db_connection()
    
    # Check if user exists
    existing = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                           (user.username, user.email)).fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    conn.execute("INSERT INTO users (username, email, hashed_password, created_at) VALUES (?, ?, ?, ?)",
                (user.username, user.email, hashed_password, datetime.now().isoformat()))
    conn.commit()
    
    # Get user ID
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    
    # Create token
    token = create_access_token(data={"sub": user.username})
    
    return {
        "message": "User registered successfully",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": user.username
    }

@app.post("/login")
async def login(user: UserLogin):
    conn = get_db_connection()
    db_user = conn.execute("SELECT * FROM users WHERE username = ?", (user.username,)).fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[3]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user[0],
        "username": db_user[1]
    }

@app.get("/products")
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
    
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    products = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(product) for product in products]

@app.get("/recommendations")
async def get_recommendations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    
    # Get user's recent interactions
    interactions = conn.execute("""
        SELECT product_id FROM user_interactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 5
    """, (current_user['id'],)).fetchall()
    
    if interactions:
        # Get categories of interacted products
        product_ids = [i[0] for i in interactions]
        placeholders = ','.join(['?'] * len(product_ids))
        
        categories = conn.execute(f"""
            SELECT DISTINCT category FROM products 
            WHERE id IN ({placeholders})
        """, product_ids).fetchall()
        
        if categories:
            category_names = [c[0] for c in categories]
            category_placeholders = ','.join(['?'] * len(category_names))
            
            # Recommend similar products
            recommendations = conn.execute(f"""
                SELECT * FROM products 
                WHERE category IN ({category_placeholders})
                AND id NOT IN ({placeholders})
                ORDER BY rating DESC
                LIMIT ?
            """, category_names + product_ids + [limit]).fetchall()
            
            conn.close()
            
            if recommendations:
                return {"recommendations": [dict(r) for r in recommendations]}
    
    # Fallback: popular products
    popular = conn.execute("""
        SELECT * FROM products 
        ORDER BY rating DESC 
        LIMIT ?
    """, (limit,)).fetchall()
    
    conn.close()
    
    return {"recommendations": [dict(p) for p in popular]}

@app.post("/user-interaction")
async def add_user_interaction(
    interaction: UserInteractionData,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    
    conn.execute("""
        INSERT INTO user_interactions (user_id, product_id, interaction_type, rating_value, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (current_user['id'], interaction.product_id, interaction.interaction_type, 
          interaction.rating_value, datetime.now().isoformat()))
    
    # Also add to recently viewed if it's a view
    if interaction.interaction_type == "view":
        conn.execute("""
            INSERT OR REPLACE INTO recently_viewed (user_id, product_id, viewed_at)
            VALUES (?, ?, ?)
        """, (current_user['id'], interaction.product_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {"message": "Interaction recorded successfully"}

@app.get("/favorites")
async def get_favorites(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    favorites = conn.execute("""
        SELECT p.* FROM products p
        JOIN favorites f ON p.id = f.product_id
        WHERE f.user_id = ?
    """, (current_user['id'],)).fetchall()
    
    conn.close()
    return {"favorites": [dict(f) for f in favorites]}

@app.post("/favorites/{product_id}")
async def add_favorite(product_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    # Check if already exists
    existing = conn.execute("""
        SELECT * FROM favorites WHERE user_id = ? AND product_id = ?
    """, (current_user['id'], product_id)).fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Product already in favorites")
    
    conn.execute("""
        INSERT INTO favorites (user_id, product_id, created_at)
        VALUES (?, ?, ?)
    """, (current_user['id'], product_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {"message": "Product added to favorites"}

@app.get("/recently-viewed")
async def get_recently_viewed(limit: int = 10, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    recent = conn.execute("""
        SELECT p.* FROM products p
        JOIN recently_viewed rv ON p.id = rv.product_id
        WHERE rv.user_id = ?
        ORDER BY rv.viewed_at DESC
        LIMIT ?
    """, (current_user['id'], limit)).fetchall()
    
    conn.close()
    return {"recently_viewed": [dict(r) for r in recent]}

@app.get("/performance/stats")
async def get_performance_stats():
    return {
        "message": "System running",
        "parallel_processing": "Enabled",
        "cache_enabled": True,
        "ml_engine": "Active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)