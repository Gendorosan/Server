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
    data = request.get_json()
    database_cursor.execute("select id from shift where id = (select max(id) from shift)")
    new_shift_id = 0
    for database_row in database_cursor:
        row = list(database_row)
        new_shift_id = int(row[0])
    print(new_shift_id)
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                            {'login': data.get('login'), 'k': new_shift_id + 1, 'date': str(now).split()[0]})

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
    data = request.args
    database_cursor.execute("select id from shift where id = (select max(id) from shift)")
    new_shift_id = 0
    for database_row in database_cursor:
        row = list(database_row)
        new_shift_id = int(row[0])
    print(new_shift_id)
    database_cursor.execute("insert into shift values(%(k)s, 'в процессе', %(login)s, %(date)s)",
                            {'login': data.get('login'), 'k': new_shift_id + 1, 'date': str(now).split()[0]})

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


@app.route("/shift_stop", methods=['POST'])
def shift_stop():
    data = request.get_json()
    database_cursor.execute("update shift set status = 'окончена' where login_worker = %(login)s",
                            {'login': data.get('login')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/shift_stop_android", methods=['GET'])
def shift_stop_android():
    data = request.args
    database_cursor.execute("update shift set status = 'окончена' where login_worker = %(login)s",
                            {'login': data.get('login')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/drop_down_list", methods=['GET'])
def drop_down_list():
    database_cursor.execute("select* from position")
    position = []
    for row in database_cursor:
        position.append({})
        i = len(position) - 1
        position[i].update([('id', row[0])])
        position[i].update([('position', str(row[1]).strip())])
        print(row[1])

    database_cursor.execute("select id, name from company")
    company = []
    for row in database_cursor:
        company.append({})
        i = len(company) - 1
        company[i].update([('id', row[0]), ('company', str(row[1]).strip())])
    return_answer = {}
    return_answer.update([('companies', company), ('positions', position)])
    return jsonify(return_answer)


@app.route("/add_coordinates", methods=['POST'])
def add_coordinates():
    data = request.get_json()
    database_cursor.execute("select id from shift where login_worker = %(login)s and status = 'в процессе'",
                            {'login': data.get('login')})
    shift_id = 0
    for row in database_cursor:
        shift_id = row[0]
        print(shift_id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s",
                            {'id': shift_id})
    i = 0
    for row in database_cursor:
        i = 0 if row[0] is None else len(row[0])
    print(i)
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(i)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': shift_id, 'i': i, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(i)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': shift_id, 'i': i, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/add_coordinates_android", methods=['GET'])
def add_coordinates_android():
    data = request.args
    database_cursor.execute("select id from shift where login_worker = %(login)s and status = 'в процессе'",
                            {'login': data.get('login')})
    shift_id = 0
    for row in database_cursor:
        shift_id = row[0]
        print(shift_id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s",
                            {'id': shift_id})
    i = 0
    for row in database_cursor:
        i = 0 if row[0] is None else len(row[0])
    print(i)
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(i)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': shift_id, 'i': i, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(i)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': shift_id, 'i': i, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/add_coordinates/coordinates_latitude", methods=['GET'])
def add_coordinates_arduino(device_number):
    data = request.args
    database_cursor.execute("select id from shift where device_number = %(device_number)s and status = 'в процессе'",
                            {'device_number': device_number})
    shift_id = 0
    for row in database_cursor:
        shift_id = row[0]
        print(shift_id)
    database_cursor.execute("select coordinates_latitude from workers_coordinates where id_shift = %(id)s",
                            {'id': shift_id})
    i = 0
    for row in database_cursor:
        i = 0 if row[0] is None else len(row[0])
    print(i)
    print(data.get('coordinates_longitude'))
    print(data.get('coordinates_latitude'))
    database_cursor.execute(
        "update workers_coordinates set coordinates_latitude[%(i)s] = %(coordinates_latitude)s where id_shift "
        "= %(id)s",
        {'id': shift_id, 'i': i, 'coordinates_latitude': data.get('coordinates_latitude')})
    database.commit()
    database_cursor.execute(
        "update workers_coordinates set coordinates_longitude[%(i)s] = %(coordinates_longitude)s where id_shift = %("
        "id)s",
        {'id': shift_id, 'i': i, 'coordinates_longitude': data.get('coordinates_longitude')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/company_registration", methods=['POST'])
def company_registration():
    try:
        print(request.get_json())
        name = request.get_json()
        database_cursor.execute('select id from company where id = (select max(id) from company)')
        company_id = 0
        for database_row in database_cursor:
            row = list(database_row)
            company_id += int(row[0])
        print(company_id)
        database_cursor.execute(
            "insert into company values(%(id)s, %(name)s, %(ogrn)s, %(inn)s, %(login)s, %(password)s)",
            {'id': company_id,
             'name': name.get('name'),
             'ogrn': name.get('ogrn'),
             'inn': name.get('inn'),
             'login': name.get('login'),
             'password': name.get('password')})
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/company_registration_android", methods=['GET'])
def company_registration_android():
    try:
        name = request.args
        database_cursor.execute('select id from company where id = (select max(id) from company)')
        company_id = 0
        for database_row in database_cursor:
            row = list(database_row)
            company_id += int(row[0])
        print(company_id)
        database_cursor.execute(
            "insert into company values(%(id)s, %(name)s, %(ogrn)s, %(inn)s, %(login)s, %(password)s)",
            {'id': company_id,
             'name': name.get('name'),
             'ogrn': name.get('ogrn'),
             'inn': name.get('inn'),
             'login': name.get('login'),
             'password': name.get('password')})
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/registration", methods=['POST'])
def registration():
    try:
        print(request.get_json())
        data = request.get_json()
        database_cursor.execute('select id from position where name = %(position)s', {'position': data.get('position')})
        position_id = 0
        for row in database_cursor:
            position_id = row[0]
        database_cursor.execute(
            "INSERT INTO workers (login, name, surname, lastname, password, phone_number, id_position, device_number) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            ((data['login']),
             (data.get('name')),
             (data.get('surname')),
             (data.get('lastname')),
             (data.get('password')),
             (data.get('phone_number')),
             position_id,
             (data.get('device_number'))))
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/registration_android", methods=['GET'])
def registration_android():
    try:
        data = request.args
        database_cursor.execute('select id from position where name = %(position)s', {'position': data.get('position')})
        position_id = 0
        for row in database_cursor:
            position_id = row[0]
        database_cursor.execute(
            "INSERT INTO workers (login, name, surname, lastname, password, phone_number, id_position, device_number) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            ((data['login']),
             (data.get('name')),
             (data.get('surname')),
             (data.get('lastname')),
             (data.get('password')),
             (data.get('phone_number')),
             position_id,
             (data.get('device_number'))))
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/authentication", methods=['POST'])
def authentication():
    try:
        print(request.get_json())
        data = request.get_json()
        database_cursor.execute("select name, surname, lastname from workers where login = %(login)s and password = "
                                "%(password)s",
                                {'login': data.get('login'),
                                 'password': data.get('password')})
        user_info = []
        for row in database_cursor:
            print(row)
            user_info.append(row)
        database_cursor.execute('select status from shift where login_worker = %(login)s', {'login': data.get('login')})
        status = []
        for row in database_cursor:
            print(row)
            status.append(row)

        return_answer = {'answer': 'success', 'name': str(user_info[0][0]).strip(),
                         'surname': str(user_info[0][1]).strip(),
                         'lastname': str(user_info[0][2]).strip(),
                         'status': str(status[-1]).strip() if len(status) > 0 else 'окончена'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/authentication_android", methods=['GET'])
def authentication_android():
    try:
        data = request.args
        database_cursor.execute("select name, surname, lastname from workers where login = %(login)s and password = "
                                "%(password)s",
                                {'login': data.get('login'),
                                 'password': data.get('password')})
        user_info = []
        for row in database_cursor:
            print(row)
            user_info.append(row)
        database_cursor.execute('select status from shift where login_worker = %(login)s', {'login': data.get('login')})
        status = []
        for row in database_cursor:
            print(row)
            status.append(row)

        return_answer = {'answer': 'success', 'name': str(user_info[0][0]).strip(),
                         'surname': str(user_info[0][1]).strip(),
                         'lastname': str(user_info[0][2]).strip(),
                         'status': str(status[-1][0]).strip() if len(status) > 0 else 'окончена'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/company_authentication", methods=['POST'])
def company_authentication():
    try:
        print(request.get_json())
        data = request.get_json()
        database_cursor.execute("select name from company where login = %(login)s and password = %(password)s",
                                {'login': data.get('login'),
                                 'password': data.get('password')})
        company_name = []
        for row in database_cursor:
            company_name.append(row)
        return_answer = {'answer': 'success', 'name': str(company_name[0][0]).strip()}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/company_authentication_android", methods=['GET'])
def company_authentication_android():
    try:
        data = request.args
        database_cursor.execute("select name from company where login = %(login)s and password = %(password)s",
                                {'login': data.get('login'),
                                 'password': data.get('password')})
        company_name = []
        for row in database_cursor:
            company_name.append(row)
        return_answer = {'answer': 'success', 'name': str(company_name[0][0]).strip()}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/statistics_1/<id>", methods=['GET'])
def statistics_1(construction_object_id):
    plt.clf()
    available_positions = []
    database_cursor.execute("select* from position")
    for database_row in database_cursor:
        row = list(database_row)
        available_positions.append(str(row[1]).strip())
    print(available_positions)

    database_cursor.execute('select id_position from workers where id_construction_object = %(id)s',
                            {'id': int(construction_object_id)})
    workers = []
    for row in database_cursor:
        print(row[0])
        workers.append(available_positions[row[0]])
    print(workers)
    amount_of_workers_on_positions = {}
    for position in set(workers):
        amount_of_workers_on_positions[position] = workers.count(position)

    data_names = []
    data_values = []
    for position in amount_of_workers_on_positions.keys():
        data_names.append(position)
        data_values.append(amount_of_workers_on_positions[position])
    print(data_values)
    print(data_names)
    dpi = 80
    fig = plt.figure(dpi=dpi, figsize=(512 / dpi, 384 / dpi))
    mpl.rcParams.update({'font.size': 9})

    plt.title('Распределение должностей на строительном объекте (%)')
    plt.pie(
        data_values, autopct='%.1f', radius=1.1,
        explode=[0.15] + [0 for _ in range(len(data_names) - 1)])
    plt.legend(
        bbox_to_anchor=(-0.16, 0.45, 0.25, 0.25),
        loc='lower left', labels=data_names)
    fig.savefig('pie.png')
    return send_from_directory(r'D:\Учеба\Питон\Server', 'pie.png')


@app.route("/statistics_2/<id>", methods=['GET'])
def statistics_2(id):
    plt.clf()
    positions = []
    database_cursor.execute("select* from position")
    position_name_bd = {}
    counts = []
    for row in database_cursor:
        position_name_bd.update([(row[0], str(row[1]).strip())])
        positions.append(str(row[1]).strip())
        counts.append(0)
    print(position_name_bd)

    database_cursor.execute('select* from workers inner join shift on workers.login = shift.login_worker inner join '
                            'construction_object on Construction_object.id = workers.id_construction_object')
    for row in database_cursor:
        counts[positions.index(position_name_bd[row[4]])] += 1
    print(counts)

    database_cursor.execute('select* from company')
    company = ''
    for row in database_cursor:
        print(row)
        if row[0] == id:
            company = str(row[1]).strip()
    plt.bar(positions, counts)
    plt.title(f"Количество рабочих смен компании '{company}'")
    plt.xlabel("Должность")
    plt.ylabel("Количество")
    plt.savefig('graph.png')
    return send_from_directory(r'D:\Учеба\Питон\Server', 'graph.png')


@app.route("/sos_signal", methods=['POST'])
def sos_signal():
    try:
        now = datetime.datetime.now()
        data = request.get_json()
        database_cursor.execute('select* from workers where login = %(login)s', {'login': data.get('login')})
        k = 0
        for row in database_cursor:
            print(row)
            k += 1
        if k == 0:
            return_answer = {'answer': 'fail'}
            return jsonify(return_answer)

        database_cursor.execute('select max(id) from sos_signal')
        new_id = 0
        for row in database_cursor:
            new_id = int(row[0]) + 1

        database_cursor.execute(
            "INSERT INTO sos_signal (login_worker, date, id) VALUES (%s, %s, %s)",
            ((data.get('login')),
             (str(now).split()[0]),
             new_id))
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)
    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/sos_signal_android", methods=['GET'])
def sos_signal_android():
    try:
        now = datetime.datetime.now()
        data = request.args
        database_cursor.execute('select* from workers where login = %(login)s', {'login': data.get('login')})
        k = 0
        for row in database_cursor:
            print(row)
            k += 1
        if k == 0:
            return_answer = {'answer': 'fail'}
            return jsonify(return_answer)

        database_cursor.execute('select max(id) from sos_signal')
        new_id = 0
        for row in database_cursor:
            new_id = int(row[0]) + 1

        database_cursor.execute(
            "INSERT INTO sos_signal (login_worker, date, id) VALUES (%s, %s, %s)",
            ((data.get('login')),
             (str(now).split()[0]),
             new_id))
        database.commit()
        return_answer = {'answer': 'success'}
        return jsonify(return_answer)

    except:
        return_answer = {'answer': 'fail'}
        return jsonify(return_answer)


@app.route("/add_construction_object", methods=['POST'])  # Тут должно быть создание записи в таблице object_coordinates
def add_construction_object():
    print(request.get_json())
    data = request.get_json()
    database_cursor.execute("select max(id) from construction_object")
    new_construction_object_id = 0
    for row in database_cursor:
        new_construction_object_id = int(row[0]) + 1
    print(new_construction_object_id)
    database_cursor.execute("insert into construction_object values(%(id)s, %(id_company)s, %(name)s)",
                            {'id': new_construction_object_id,
                             'id_company': data.get('id'),
                             'name': data.get('name')})
    database.commit()
    database_cursor.execute('select max(id) from object_coordinates')
    new_object_coordinates_id = 0
    for row in database_cursor:
        new_object_coordinates_id = int(row[0]) + 1
    database_cursor.execute(
        'insert into object_coordinates values(%(object_coordinates_id)s, %(coordinates_latitude)s, '
        '%(construction_object_id)s, %(coordinated_longitude)s)', {
            'object_coordinates_id': new_object_coordinates_id,
            'coordinates_latitude': data.get('coordinates_latitude'),
            'construction_object_id': new_construction_object_id,
            'coordinated_longitude': data.get('coordinated_longitude')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


@app.route("/add_construction_object_android",
           methods=['GET'])  # Тут должно быть создание записи в таблице object_coordinates
def add_construction_object_android():
    data = request.args
    database_cursor.execute("select max(id) from construction_object")
    new_construction_object_id = 0
    for row in database_cursor:
        new_construction_object_id = int(row[0]) + 1
    print(new_construction_object_id)
    database_cursor.execute("insert into construction_object values(%(id)s, %(id_company)s, %(name)s)",
                            {'id': new_construction_object_id,
                             'id_company': data.get('id'),
                             'name': data.get('name')})
    database.commit()
    database_cursor.execute('select max(id) from object_coordinates')
    new_object_coordinates_id = 0
    for row in database_cursor:
        new_object_coordinates_id = int(row[0]) + 1
    database_cursor.execute(
        'insert into object_coordinates values(%(object_coordinates_id)s, %(coordinates_latitude)s, '
        '%(construction_object_id)s, %(coordinated_longitude)s)', {
            'object_coordinates_id': new_object_coordinates_id,
            'coordinates_latitude': data.get('coordinates_latitude'),
            'construction_object_id': new_construction_object_id,
            'coordinated_longitude': data.get('coordinated_longitude')})
    database.commit()
    return_answer = {'answer': 'success'}
    return jsonify(return_answer)


if __name__ == "__main__":
    app.run(debug=True)
