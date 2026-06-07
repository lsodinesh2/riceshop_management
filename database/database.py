import os
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("mysql.railway.internal"),
        user=os.environ.get("root"),
        password=os.environ.get("EEnIJRGNIZJpQeBEtXlvcVnllyflqhmR"),
        database=os.environ.get("railway"),
        port=int(os.environ.get("3306", 3306))
    )
