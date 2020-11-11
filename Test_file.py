from flask import Flask, jsonify, request
import psycopg2
import datetime

database = psycopg2.connect(database='Server', user='postgres', password=' ', host='127.0.0.1', port=5432)
database_cursor = database.cursor()
all = 'status'

data = {'login': 'nya', 'password': 'qwerty'}
database_cursor.execute(f"select name, surname, lastname from workers "
                        f"where login = '{data['login']}' and password = 'qwerty'")
for row in database_cursor:
    print(row)