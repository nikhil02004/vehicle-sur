#!/usr/bin/env python3
"""
Test database connection with environment variables
"""

from dotenv import load_dotenv
import os
import mysql.connector

def test_db_connection():
    load_dotenv()
    
    print("🔧 Testing Database Connection")
    print("=" * 40)
    
    # Get environment variables
    host = os.getenv('MYSQL_HOST')
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    database = os.getenv('MYSQL_DATABASE')
    
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Password: {'Set' if password else 'Not set'}")
    print()
    
    try:
        print("Attempting connection...")
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        print("✅ Database connection successful!")
        
        # Test a simple query
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database connection failed: {err}")
        print("\n💡 Possible solutions:")
        print("1. Make sure MySQL server is running")
        print("2. Check if the database 'numberplates_speed' exists")
        print("3. Verify the password is correct")
        print("4. Ensure the user 'root' has access to the database")

if __name__ == "__main__":
    test_db_connection()
