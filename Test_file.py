from flask import Flask, jsonify, request
import psycopg2
import datetime


database = psycopg2.connect(database='Server', user='postgres', password=' ', host='127.0.0.1', port=5432)
database_cursor = database.cursor()


def shift_start():
    now = datetime.datetime.now()
    login = {'login': 'nya'}
    database_cursor.execute("select id from shift where id = (select max(id) from shift)")
    id_shift = 0
    for _ in database_cursor:
        id_shift += 1
    print(str(now).split()[0])
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                            {'login': login.get('login'), 'k': id_shift, 'date': str(now).split()[0]})

    database.commit()
    database_cursor.execute("select* from workers_coordinates")
    k = 0
    for _ in database_cursor:
        k += 1
    print(k)
    database_cursor.execute('insert into workers_coordinates values(%(id)s, %(first)s, %(id_shift)s)',
                            {'id': k, 'first': None, 'id_shift': id_shift})
    database.commit()
    dict = {'answer': 'success'}
    print(dict)


shift_start()
