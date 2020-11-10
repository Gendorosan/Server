from flask import Flask, jsonify, request
import psycopg2
import datetime

database = psycopg2.connect(database='Server', user='postgres', password=' ', host='127.0.0.1', port=5432)
database_cursor = database.cursor()

database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift=2")
print(database_cursor)

for row in database_cursor:
    i = 0 if row[0] is None else len(row[0])
print(i)
