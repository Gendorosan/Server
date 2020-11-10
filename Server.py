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
    return_answer = {}
    database_cursor.execute("SELECT name, surname, lastname FROM workers WHERE surname "
                            "= %(surname)s", {'surname': surname.get('surname')})
    for database_row in database_cursor:
        row = list(database_row)
        return_answer.update([(row[0], {'name': row[1], 'surname': row[2], 'lastname': row[3]})])
    return jsonify(return_answer)


@app.route("/all_workers_on_construction_object_without_status/<id>", methods=['GET'])
def all_workers_on_construction_object_without_status(construction_object_id):
    return_answer = {}
    database_cursor.execute("select name, surname, lastname from workers where id_construction_object in"
                            " (select  id from construction_object where id = %(id)s", {'id': construction_object_id})
    for database_row in database_cursor:
        row = list(database_row)
        return_answer.update([(row[0], {'name': row[1], 'surname': row[2], 'lastname': row[3]})])
    return jsonify(return_answer)


@app.route("/all_workers_on_construction_object/<id>", methods=['GET'])
def all_workers_on_construction_object(construction_object_id):
    available_positions = []
    database_cursor.execute("select* from position")
    for database_row in database_cursor:
        row = list(database_row)
        available_positions.append(str(row[1]).strip())

    database_cursor.execute(
        "select* from workers inner join shift on workers.login = shift.login_worker where id_construction_object = "
        "%(id)s", {'id': int(construction_object_id)})
    return_answer = {}
    index = 0
    for database_row in database_cursor:
        row = list(database_row)
        login = str(row[0]).strip()
        name = str(row[1]).strip()
        surname = str(row[2]).strip()
        lastname = str(row[3]).strip()
        status = str(row[10]).strip()
        date = str(row[12]).strip()
        worker_to_add = {}
        worker_to_add.update([('login', login), ('name', name), ('surname', surname), ('lastname', lastname),
                              ('position', available_positions[int(row[4].strip())]), ('status', status),
                              ('date', date)])
        if all(worker_to_add['login'] != value['login'] for key, value in return_answer.items()):
            return_answer.update([(index, worker_to_add)])
            index += 1
        for key, value in return_answer.items():
            if value['login'] == worker_to_add['login'] and worker_to_add['status'] == 'в процессе':
                return_answer.update([(key, worker_to_add)])
    return jsonify(return_answer)


@app.route("/shift_start", methods=['POST'])
def shift_start():
    now = datetime.datetime.now()
    login = request.get_json()
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
    return jsonify(return_answer)


@app.route("/shift_start_android", methods=['GET'])
def shift_start_android():
    now = datetime.datetime.now()
    login = request.args
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
    return jsonify(dict)


@app.route("/shift_stop", methods=['POST'])
def shift_stop():
    login = request.get_json()
    database_cursor.execute("update shift set status = 'окончена' where login_worker = %(login)s",
                            {'login': login.get('login')})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/shift_stop_android", methods=['GET'])
def shift_stop_android():
    login = request.args
    database_cursor.execute("update shift set status = 'окончена' where login_worker = %(login)s",
                            {'login': login.get('login')})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/drop_down_list", methods=['GET'])
def drop_down_list():
    database_cursor.execute("select* from position")
    position = [{}]
    i = 0
    for row in database_cursor:
        position.append({})
        print(i)
        position[i].update([('id', row[0])])
        position[i].update([('position', str(row[1]).strip())])
        print(row[1])
        i += 1
    position.pop(i)
    database_cursor.execute("select id, name from company")
    company = [{}]
    i = 0
    for row in database_cursor:
        company.append({})
        company[i].update([('id', row[0]), ('company', str(row[1]).strip())])
        i += 1
    company.pop(i)
    out = {}
    out.update([('companies', company), ('positions', position)])
    return jsonify(out)


@app.route("/add_coordinates", methods=['POST'])
def add_coordinates():
    data = request.get_json()
    database_cursor.execute("select id from shift where login_worker = %(login)s and status = 'в процессе'",
                            {'login': data.get('login')})
    id = 0
    for row in database_cursor:
        id = row[0]
        print(id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s", {'id': id})
    k = 0
    try:
        for row in database_cursor:
            k = len(row[0])
        print(k)
    except:
        k = 0
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(k)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': id, 'k': k, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(k)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': id, 'k': k, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/add_coordinates_android", methods=['GET'])
def add_coordinates_android():
    data = request.args
    database_cursor.execute("select id from shift where login_worker = %(login)s and status = 'в процессе'",
                            {'login': data.get('login')})
    id = 0
    for row in database_cursor:
        id = row[0]
        print(id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s", {'id': id})
    k = 0
    try:
        for row in database_cursor:
            k = len(row[0])
        print(k)
    except:
        k = 0
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(k)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': id, 'k': k, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(k)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': id, 'k': k, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/add_coordinates/coordinates_latitude", methods=['GET'])
def add_coordinates_arduino(device_number):
    data = request.args
    database_cursor.execute("select id from shift where device_number = %(device_number)s and status = 'в процессе'",
                            {'device_number': device_number})
    id = 0
    for row in database_cursor:
        id = row[0]
        print(id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s", {'id': id})
    k = 0
    try:
        for row in database_cursor:
            k = len(row[0])
        print(k)
    except:
        k = 0
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(k)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': id, 'k': k, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(k)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': id, 'k': k, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    dict = {'answer': 'success'}
    return jsonify(dict)


@app.route("/company_registration", methods=['POST'])
def company_registration():
    try:
        print(request.get_json())
        name = request.get_json()
        database_cursor.execute('select* from company')
        k = 0
        for _ in database_cursor:
            k += 1
        print(k)
        database_cursor.execute(
            "insert into company values(%(id)s, %(name)s, %(ogrn)s, %(inn)s, %(login)s, %(password)s)",
            {'id': k,
             'name': name.get('name'),
             'ogrn': name.get('ogrn'),
             'inn': name.get('inn'),
             'login': name.get('login'),
             'password': name.get('password')})
        database.commit()
        dict = {'answer': 'success'}
        return jsonify(dict)
    except:
        dict = {'answer': 'fail'}
        return jsonify(dict)


@app.route("/company_registration_android", methods=['GET'])
def company_registration_android():
    try:
        name = request.args
        database_cursor.execute('select* from company')
        k = 0
        for _ in database_cursor:
            k += 1
        print(k)
        database_cursor.execute(
            "insert into company values(%(id)s, %(name)s, %(ogrn)s, %(inn)s, %(login)s, %(password)s)",
            {'id': k,
             'name': name.get('name'),
             'ogrn': name.get('ogrn'),
             'inn': name.get('inn'),
             'login': name.get('login'),
             'password': name.get('password')})
        database.commit()
        dict = {'answer': 'success'}
        return jsonify(dict)
    except:
        dict = {'answer': 'fail'}
        return jsonify(dict)


if __name__ == "__main__":
    app.run(debug=True)
