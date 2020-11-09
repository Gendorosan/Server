from flask import Flask, jsonify, request
from flask import send_from_directory
import psycopg2
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use('Agg')

app = Flask(__name__)

conn = psycopg2.connect(database='hackathon', user='postgres', password='gennadi0', host='127.0.0.1', port=5432)
cur = conn.cursor()


@app.route("/update", methods=['POST'])
def update():
    dict = {}
    print(request.get_json())
    name = request.get_json()
    cur.execute("INSERT INTO workers (id, name, surname) VALUES (%s, %s, %s)", (name.get('id'), (name.get('name')),
                                                                                name.get('surname')))
    conn.commit()
    dict.update([('name', name.get('name'))])  # Надо бы в бд занести
    dict.update([('surname', name.get('surname'))])
    dict.update([('coordinates', name.get('coordinates'))])
    return jsonify(dict)


@app.route("/all_workers", methods=['GET'])
def all_workers():
    out = []
    dict = {}
    cur.execute("SELECT* FROM workers")
    for row in cur:
        out.append(list(row))
    for i in range(len(out)):
        out_dict = {'name': out[i][1],
                    'surname': out[i][2]}
        dict.update([(out[i][0], out_dict)])
    return jsonify(dict)


@app.route("/find_worker/<login>", methods=['GET'])
def find_worker_id(login):
    out = []
    dict = {}
    cur.execute("SELECT* FROM workers WHERE login = %(login)s", {'login': login})
    for row in cur:
        out.append(list(row))
    for i in range(len(out)):
        out_dict = {'name': out[i][1],
                    'surname': out[i][2]}
        dict.update([(out[i][0], out_dict)])
    return jsonify(dict)


@app.route("/find_worker", methods=['POST'])
def find_worker_surname():
    surname = request.get_json()
    out = []
    dict = {}
    cur.execute("SELECT name, surname, lastname FROM workers WHERE surname "
                "= %(surname)s", {'surname': surname.get('surname')})
    for row in cur:
        out.append(list(row))
    for i in range(len(out)):
        out_dict = {'name': out[i][1],
                    'surname': out[i][2],
                    'lastname': out[i][3]}
        dict.update([(out[i][0], out_dict)])
    return jsonify(dict)


@app.route("/location", methods=['POST'])
def location():
    out = []
    dict = {}
    data = request.get_json()
    cur.execute("select* from workers inner join object_coordinates on object_coordinates.id_construction_object = "
                "workers.id_construction_object inner join shift on shift.login_worker = workers.login")
    for row in cur:
        out.append(list(row))
    shift_id = ''
    for i in range(len(out)):
        if str(out[i][0]).strip() == data.get('login') and str(out[i][14]).strip() == 'окончена':
            dict.update([('values_latitude', out[i][10]),
                         ('values_longitude', out[i][12])])
            print(dict)
            return jsonify(dict)
        if str(out[i][0]).strip() == data.get('login') and str(out[i][14]).strip() == 'в процессе':
            shift_id = str(out[i][13]).strip()
            dict.update([('values_latitude', out[i][10]),
                         ('values_longitude', out[i][12])])
    cur.execute("select* from workers_coordinates where id_shift = %(id)s", {'id': shift_id})
    print(shift_id)
    print(dict)
    for row in cur:
        dict.update([('coordinates_latitude', row[1][len(row[1]) - 1]),
                     ('coordinates_longitude', row[3][len(row[3]) - 1])])
        return jsonify(dict)


if __name__ == "__main__":
    app.run(debug=True)