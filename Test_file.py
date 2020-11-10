from flask import Flask, jsonify, request
import psycopg2
import datetime


database = psycopg2.connect(database='Server', user='postgres', password=' ', host='127.0.0.1', port=5432)
database_cursor = database.cursor()


def shift_start():
    now = datetime.datetime.now()
    login = {'login': 'nya'}
    database_cursor.execute("select id from shift where id = (select max(id) from shift)")
    new_shift_id = 0
    for database_row in database_cursor:
        row = list(database_row)
        new_shift_id = int(row[0])
    print(new_shift_id)
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                            {'login': login.get('login'), 'k': new_shift_id + 1, 'date': str(now).split()[0]})

    database.commit()
    database_cursor.execute("select id from workers_coordinates where id = (select max(id) from workers_coordinates)")
    new_workers_coordinates_id = 0
    for database_row in database_cursor:
        row = list(database_row)
        new_workers_coordinates_id = int(row[0])
    print(new_workers_coordinates_id)
    database_cursor.execute('insert into workers_coordinates values(%(id)s, %(first)s, %(id_shift)s)',
                            {'id': new_workers_coordinates_id + 1, 'first': None, 'id_shift': new_shift_id + 1})
    database.commit()
    return_answer = {'answer': 'success'}
    print(return_answer)


shift_start()
