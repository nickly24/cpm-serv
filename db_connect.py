import mysql.connector
from flask import Flask, jsonify

def get_db_connection():
    return mysql.connector.connect(
        host="147.45.138.77",
        port=3306,
        user="minishep",
        database="minishep",
        password="qwerty!1"
    )





