import mysql.connector

db_config = {
    'user': 'root',
    'password': 'hemant',
    'host': '192.168.1.18',
    'port': 3306,
    'database': 'test'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)
