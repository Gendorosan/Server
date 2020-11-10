from flask import Flask, jsonify, request
from flask import send_from_directory
import psycopg2
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use('Agg')

app = Flask(__name__)

database = psycopg2.connect(database='Server', user='postgres', password=' ', host='127.0.0.1', port=5432)
database_cursor = database.cursor()


@app.route("/update", methods=['POST'])
def update():
    print(request.get_json())
    data = request.get_json()
    database_cursor.execute("INSERT INTO workers (id, name, surname) VALUES (%s, %s, %s)", (data.get('id'),
                                                                                            (data.get('name')),
                                                                                            data.get('surname')))
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/all_workers", methods=['GET'])
def all_workers():
    return_answer = {}
    database_cursor.execute("SELECT* FROM workers")
    for database_row in database_cursor:
        row = list(database_row)
        return_answer.update([(row[0], {'name': row[1], 'surname': row[2]})])
    return jsonify(return_answer)


@app.route("/find_worker/<login>", methods=['GET'])
def find_worker_id(login):
    return_answer = {}
    database_cursor.execute("SELECT* FROM workers WHERE login = %(login)s", {'login': login})
    for database_row in database_cursor:
        row = list(database_row)
        return_answer.update([(row[0], {'name': row[1], 'surname': row[2]})])
    return jsonify(return_answer)


@app.route("/find_worker", methods=['POST'])
def find_worker_surname():
    surname = request.get_json()
    return_answer = {}
    database_cursor.execute("SELECT name, surname, lastname FROM workers WHERE surname "
                            "= %(surname)s", {'surname': surname.get('surname')})
    for database_row in database_cursor:
        row = list(database_row)
        return_answer.update([(row[0], {'name': row[1], 'surname': row[2], 'lastname': row[3]})])
    return jsonify(return_answer)


@app.route("/location", methods=['POST'])
def location():
    return_answer = {}
    shift_id = ''
    data = request.get_json()
    database_cursor.execute(
        "select* from workers inner join object_coordinates on object_coordinates.id_construction_object = "
        "workers.id_construction_object inner join shift on shift.login_worker = workers.login")
    for database_row in database_cursor:
        row = list(database_row)
        login = str(row[0]).strip()
        shift_status = str(row[14]).strip()
        latitude = row[10]
        longitude = row[12]
        if login == data.get('login') and shift_status == 'окончена':
            return_answer.update([('values_latitude', latitude), ('values_longitude', longitude)])
            return jsonify(return_answer)
        elif login == 'login' and shift_status == 'в процессе':
            shift_id = str(row[13]).strip()
            return_answer.update([('values_latitude', latitude), ('values_longitude', longitude)])
    print(shift_id)
    print(return_answer)

    database_cursor.execute("select* from workers_coordinates where id_shift = %(id)s", {'id': shift_id})
    for row in database_cursor:
        return_answer.update([('coordinates_latitude', row[1][len(row[1]) - 1]),
                              ('coordinates_longitude', row[3][len(row[3]) - 1])])
    return jsonify(return_answer)


@app.route("/find_worker_android", methods=['GET'])
def find_worker_surname_android():
    surname = request.args
    out = []
    dict = {}
    database_cursor.execute("SELECT name, surname, lastname FROM workers WHERE surname "
                "= %(surname)s", {'surname': surname.get('surname')})
    for row in database_cursor:
        out.append(list(row))
    for i in range(len(out)):
        out_dict = {'name': out[i][1],
                    'surname': out[i][2],
                    'lastname': out[i][3]}
        dict.update([(out[i][0], out_dict)])
    return jsonify(dict)


@app.route("/all_workers_on_construction_object_without_status/<id>", methods=['GET'])
def all_workers_on_construction_object_without_status(id):
    out = []
    dict = {}
    database_cursor.execute("select name, surname, lastname from workers where id_construction_object in"
                " (select  id from construction_object where id = %(id)s", {'id': id})
    for row in database_cursor:
        out.append(list(row))
    for i in range(len(out)):
        out_dict = {'name': out[i][1],
                    'surname': out[i][2],
                    'lastname': out[i][3]}
        dict.update([(out[i][0], out_dict)])
    return jsonify(dict)


@app.route("/all_workers_on_construction_object/<id>", methods=['GET'])
def all_workers_on_construction_object(id):
    list_position = []
    database_cursor.execute("select* from position")
    for row in database_cursor:
        for i in range(len(row)):
            if i / 2 != 0:
                list_position.append(str(row[i]).strip())
    database_cursor.execute(
        "select* from workers inner join shift on workers.login = shift.login_worker where id_construction_object = "
        "%(id)s", {'id': int(id)})
    out_list = []
    list_to_strip = []
    for row in database_cursor:
        list_to_strip = []
        for i in range(len(row)):
            list_to_strip.append(str(row[i]).strip())
        out_list.append(list_to_strip)
    print(out_list)
    all_workers = {}
    index = 0
    for worker in out_list:
        worker_to_add = {}
        print(worker[4])
        worker_to_add.update([('login', worker[0]),
                              ('name', worker[1]),
                              ('surname', worker[2]),
                              ('lastname', worker[3]),
                              ('position', list_position[int(worker[4].strip())]),
                              ('status', worker[10]),
                              ('date', worker[12])])
        if all(worker_to_add['login'] != value['login'] for key, value in all_workers.items()):
            all_workers.update([(index, worker_to_add)])
            index += 1
        for key, value in all_workers.items():
            if value['login'] == worker_to_add['login'] and worker_to_add['status'] == 'в процессе':
                all_workers.update([(key, worker_to_add)])
    return jsonify(all_workers)


@app.route("/shift_start", methods=['POST'])
def shift_start():
    now = datetime.datetime.now()
    login = request.get_json()
    database_cursor.execute("select id from shift")
    id_shift = 0
    for row in database_cursor:
        id_shift += 1
    print(id_shift)
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                {'login': login.get('login'), 'k': id_shift, 'date': str(now).split()[0]})
    database.commit()
    database_cursor.execute("select* from workers_coordinates")
    k = 0
    for row in database_cursor:
        k += 1
    print(k)
    database_cursor.execute('insert into workers_coordinates values(%(id)s, %(first)s, %(id_shift)s)',
                {'id': k, 'first': None, 'id_shift': id_shift})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/shift_start_android", methods=['GET'])
def shift_start_android():
    now = datetime.datetime.now()
    login = request.args
    database_cursor.execute("select id from shift")
    id_shift = 0
    for row in database_cursor:
        id_shift += 1
    print(id_shift)
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                {'login': login.get('login'), 'k': id_shift, 'date': str(now).split()[0]})
    database.commit()
    database_cursor.execute("select* from workers_coordinates")
    k = 0
    for row in database_cursor:
        k += 1
    print(k)
    database_cursor.execute('insert into workers_coordinates values(%(id)s, %(first)s, %(id_shift)s)',
                {'id': k, 'first': None, 'id_shift': id_shift})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


if __name__ == "__main__":
    app.run(debug=True)
