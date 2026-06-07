import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="mysql.railway.internal",
        user="root",
        password="EEnIJRGNIZJpQeBEtXlvcVnllyflqhmR",
        database="railway",
        port=3306
    )