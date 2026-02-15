import mysql.connector
from mysql.connector import Error

config = {
    'user': 'root',
    'password': 'hemant',
    'host': '192.168.0.7',
    'port': 3306,
    'database': 'test'
}

connection = None   # ✅ Define before try block

try:
    connection = mysql.connector.connect(**config)
    
    if connection.is_connected():
        db_info = connection.get_server_info()
        print(f"Connected to MySQL database version: {db_info}")
        
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print(f"You're connected to database: {record[0]}")
        
except Error as e:
    print(f"Error connecting to MySQL database: {e}")

finally:
    # ✅ Check if connection exists AND is connected
    if connection is not None and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
