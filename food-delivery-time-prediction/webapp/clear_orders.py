import sqlite3

# Connect to your database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Delete all rows from the users table
cursor.execute("DELETE FROM users")

# 2. Reset the ID counter so your next order starts at #1001 again!
cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")

# Save and close
conn.commit()
conn.close()

print("✅ The Orders table has been completely emptied!")