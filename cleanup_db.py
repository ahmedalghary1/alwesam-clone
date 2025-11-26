import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Delete all products
cursor.execute("DELETE FROM products_product")
cursor.execute("DELETE FROM products_productimages")
cursor.execute("DELETE FROM products_review")

# Commit changes
conn.commit()

# Verify deletion
cursor.execute("SELECT COUNT(*) FROM products_product")
count = cursor.fetchone()[0]
print(f"Products remaining: {count}")

conn.close()
print("Database cleaned successfully!")
