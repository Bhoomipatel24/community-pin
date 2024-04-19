import mysql.connector
from werkzeug.security import generate_password_hash
import config

email = "admin@example.com"
password = generate_password_hash("admin_password", method='pbkdf2:sha256')
role = "admin"

admin_query = """
    INSERT INTO users (email, password, role)
    VALUES (%s, %s, %s)
"""

db_config = {
    'host': config.MYSQL_HOST,
    'user': config.MYSQL_USER,
    'password': config.MYSQL_PASSWORD,
    'database': config.MYSQL_DB,
}




try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(admin_query, (email, password, role))
    conn.commit()
except Exception as e:
    print("Error occurred", e)