from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination, get_page_args
from datetime import datetime
import os
import json

app = Flask(__name__)

# Zakomentowane: Konfiguracja połączenia z bazą danych Oracle
# app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+cx_oracle://username:password@hostname:port/dbname'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# Zakomentowane: Definicje modeli bazy danych
# class Process(db.Model):
#     __tablename__ = 'processes'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, nullable=False)

# class Transaction(db.Model):
#     __tablename__ = 'transactions'
#     id = db.Column(db.Integer, primary_key=True)
#     process_id = db.Column(db.Integer, db.ForeignKey('processes.id'))
#     terminal_id = db.Column(db.String, nullable=False)
#     response_code = db.Column(db.String, nullable=False)
#     date_time = db.Column(db.DateTime, nullable=False)
#     auth_code = db.Column(db.String, nullable=False)

DATA_FILE = 'data.txt'

# Mock data functions
def read_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {'processes': [], 'transactions': []}

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def generate_mock_data():
    data = {
        'processes': [
            {'id': 1, 'name': 'Process 1'},
            {'id': 2, 'name': 'Process 2'}
        ],
        'transactions': [
            {'id': 1, 'process_id': 1, 'terminal_id': 'T1', 'response_code': '000', 'date_time': '2023-07-22T10:00:00', 'auth_code': 'A1'},
            {'id': 2, 'process_id': 1, 'terminal_id': 'T2', 'response_code': '001', 'date_time': '2023-07-22T11:00:00', 'auth_code': 'A2'},
            {'id': 3, 'process_id': 2, 'terminal_id': 'T1', 'response_code': '066', 'date_time': '2023-07-22T12:00:00', 'auth_code': 'A3'},
            {'id': 4, 'process_id': 2, 'terminal_id': 'T2', 'response_code': '096', 'date_time': '2023-07-22T13:00:00', 'auth_code': 'A4'}
        ]
    }
    write_data(data)

generate_mock_data()

@app.route('/')
def index():
    try:
        data = read_data()
        processes = data['processes']
        transactions = data['transactions']

        # Calculate counts and totals
        process_counts = {}
        response_codes = set()  # Collect all unique response codes
        for transaction in transactions:
            process_id = transaction['process_id']
            response_code = transaction['response_code']
            response_codes.add(response_code)  # Add response code to the set
            if process_id not in process_counts:
                process_counts[process_id] = {'total': 0}
            process_counts[process_id]['total'] += 1
            if response_code not in process_counts[process_id]:
                process_counts[process_id][response_code] = 0
            process_counts[process_id][response_code] += 1

        # Convert response_codes to a sorted list
        response_codes = sorted(response_codes)

        # Prepare process data for rendering
        process_data = []
        for process in processes:
            pid = process['id']
            counts = process_counts.get(pid, {'total': 0})
            row = [process['name'], counts.get('total', 0)]
            for code in response_codes:
                row.append(counts.get(code, 0))
            process_data.append(row)

        # Calculate totals
        totals = {'total': sum(counts.get('total', 0) for counts in process_counts.values())}
        for code in response_codes:
            totals[code] = sum(counts.get(code, 0) for counts in process_counts.values())

        return render_template('index.html', processes=process_data, totals=totals, response_codes=response_codes)
    except Exception as e:
        return str(e), 500

@app.route('/process/<int:process_id>')
def process_detail(process_id):
    try:
        data = read_data()
        processes = data['processes']
        transactions = data['transactions']

        process = next((p for p in processes if p['id'] == process_id), None)
        if not process:
            return "Process not found", 404

        page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = per_page or 30
        filtered_transactions = [t for t in transactions if t['process_id'] == process_id]
        total = len(filtered_transactions)
        transactions_page = filtered_transactions[(page - 1) * per_page: page * per_page]

        pagination = Pagination(page=page, total=total, record_name='transactions', per_page=per_page)
        return render_template('process_detail.html', process=process, transactions=transactions_page, pagination=pagination)
    except Exception as e:
        return str(e), 500

@app.route('/terminal/<string:terminal_id>')
def terminal_detail(terminal_id):
    try:
        data = read_data()
        transactions = data['transactions']

        page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = per_page or 30
        filtered_transactions = [t for t in transactions if t['terminal_id'] == terminal_id]
        total = len(filtered_transactions)
        transactions_page = filtered_transactions[(page - 1) * per_page: page * per_page]

        pagination = Pagination(page=page, total=total, record_name='transactions', per_page=per_page)
        return render_template('terminal_detail.html', terminal_id=terminal_id, transactions=transactions_page, pagination=pagination)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)


# app.config['SQLALCHEMY_DATABASE_URI'] = f'oracle+cx_oracle://{username}:{password}@{hostname}:{port}/{service_name}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# Define database models
# class Process(db.Model):
#     __tablename__ = 'processes'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, nullable=False)

# class Transaction(db.Model):
#     __tablename__ = 'transactions'
#     id = db.Column(db.Integer, primary_key=True)
#     process_id = db.Column(db.Integer, db.ForeignKey('processes.id'))
#     terminal_id = db.Column(db.String, nullable=False)
#     response_code = db.Column(db.String, nullable=False)
#     date_time = db.Column(db.DateTime, nullable=False)
#     auth_code = db.Column(db.String, nullable=False)
