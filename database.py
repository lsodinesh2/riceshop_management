import os
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host=os.getenv("centerbeam.proxy.rlwy.net"),
        user=os.getenv("root"),
        password=os.getenv("EEnIJRGNIZJpQeBEtXlvcVnllyflqhmR"),
        database=os.getenv("railway"),
        port=int(os.getenv("21946"))
    )