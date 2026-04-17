import sqlite3
import random
from faker import Faker
import pandas as pd
from datetime import datetime, timedelta

fake = Faker()

# Product categories
CATEGORIES = [
    "Electronics", "Clothing", "Books", "Home & Garden", 
    "Sports", "Toys", "Beauty", "Automotive", "Health", "Groceries"
]

# Product names by category
PRODUCT_NAMES = {
    "Electronics": ["Smartphone", "Laptop", "Tablet", "Headphones", "Smart Watch", "Camera", "TV", "Speaker", "Gaming Console", "Drone"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Dress", "Shoes", "Hat", "Scarf", "Sweater", "Shorts", "Skirt"],
    "Books": ["Novel", "Textbook", "Cookbook", "Biography", "Self-Help", "Science Fiction", "Mystery", "Poetry", "History", "Art Book"],
    "Home & Garden": ["Sofa", "Table", "Chair", "Lamp", "Plant", "Rug", "Curtains", "Pillow", "Vase", "Garden Tools"],
    "Sports": ["Football", "Basketball", "Tennis Racket", "Yoga Mat", "Running Shoes", "Bicycle", "Dumbbells", "Swim Goggles", "Ski Poles", "Camping Tent"],
    "Toys": ["LEGO Set", "Doll", "Action Figure", "Board Game", "Puzzle", "Stuffed Animal", "Remote Control Car", "Play-Doh", "Kite", "Train Set"],
    "Beauty": ["Lipstick", "Foundation", "Mascara", "Shampoo", "Conditioner", "Moisturizer", "Perfume", "Nail Polish", "Hair Dryer", "Makeup Brush Set"],
    "Automotive": ["Car Wax", "Oil Filter", "Tire", "Car Charger", "Floor Mats", "GPS", "Seat Covers", "Steering Wheel Cover", "Car Vacuum", "Tool Set"],
    "Health": ["Vitamins", "Protein Powder", "First Aid Kit", "Massager", "Blood Pressure Monitor", "Yoga Ball", "Resistance Bands", "Pill Organizer", "Thermometer", "Foot Spa"],
    "Groceries": ["Coffee", "Tea", "Snacks", "Pasta", "Rice", "Canned Goods", "Frozen Vegetables", "Spices", "Cooking Oil", "Sauce"]
}

def generate_products(num_products=100):
    """Generate synthetic products"""
    products = []
    
    for i in range(num_products):
        category = random.choice(CATEGORIES)
        product_name = random.choice(PRODUCT_NAMES[category])
        
        product = {
            'id': i + 1,
            'name': f"{product_name} {fake.word().capitalize()}",
            'description': fake.text(max_nb_chars=200),
            'price': round(random.uniform(10, 500), 2),
            'category': category,
            'image_url': f"https://picsum.photos/id/{random.randint(1, 100)}/300/200",
            'rating': round(random.uniform(0, 5), 1),
            'stock': random.randint(0, 1000),
            'created_at': datetime.now().isoformat()
        }
        products.append(product)
    
    return products

def generate_users(num_users=50):
    """Generate synthetic users"""
    users = []
    
    for i in range(num_users):
        user = {
            'id': i + 1,
            'username': fake.user_name(),
            'email': fake.email(),
            'hashed_password': 'hashed_password_placeholder',
            'created_at': datetime.now().isoformat()
        }
        users.append(user)
    
    return users

def generate_interactions(users, products, num_interactions=500):
    """Generate synthetic user-product interactions"""
    interactions = []
    interaction_types = ['view', 'click', 'purchase', 'rating']
    
    for i in range(num_interactions):
        user = random.choice(users)
        product = random.choice(products)
        
        interaction = {
            'id': i + 1,
            'user_id': user['id'],
            'product_id': product['id'],
            'interaction_type': random.choice(interaction_types),
            'rating_value': round(random.uniform(1, 5), 1) if random.random() > 0.7 else None,
            'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        }
        interactions.append(interaction)
    
    return interactions

def create_database():
    """Create SQLite database with synthetic data"""
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            hashed_password TEXT,
            created_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            image_url TEXT,
            rating REAL,
            stock INTEGER,
            created_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS user_interactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            interaction_type TEXT,
            rating_value REAL,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        
        CREATE TABLE IF NOT EXISTS recently_viewed (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            viewed_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    ''')
    
    # Generate and insert data
    products = generate_products(100)
    users = generate_users(50)
    interactions = generate_interactions(users, products, 500)
    
    # Insert products
    for product in products:
        cursor.execute('''
            INSERT INTO products (id, name, description, price, category, image_url, rating, stock, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product['id'], product['name'], product['description'], 
              product['price'], product['category'], product['image_url'],
              product['rating'], product['stock'], product['created_at']))
    
    # Insert users
    for user in users:
        cursor.execute('''
            INSERT INTO users (id, username, email, hashed_password, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], user['username'], user['email'], 
              user['hashed_password'], user['created_at']))
    
    # Insert interactions
    for interaction in interactions:
        cursor.execute('''
            INSERT INTO user_interactions (id, user_id, product_id, interaction_type, rating_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (interaction['id'], interaction['user_id'], interaction['product_id'],
              interaction['interaction_type'], interaction['rating_value'], interaction['timestamp']))
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully!")
    print(f"  - {len(products)} products")
    print(f"  - {len(users)} users")
    print(f"  - {len(interactions)} interactions")

if __name__ == "__main__":
    create_database()