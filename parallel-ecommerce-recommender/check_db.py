import sqlite3

conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Check products
cursor.execute("SELECT COUNT(*) FROM products")
product_count = cursor.fetchone()[0]
print(f"Products in database: {product_count}")

# Show first 5 products
cursor.execute("SELECT id, name, price, category FROM products LIMIT 5")
products = cursor.fetchall()
print("\nFirst 5 products:")
for product in products:
    print(f"  ID: {product[0]}, Name: {product[1]}, Price: ${product[2]}, Category: {product[3]}")

# Check users
cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
print(f"\nUsers in database: {user_count}")

conn.close()