from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import csv
from io import StringIO, BytesIO

app = Flask(__name__)
CORS(app)

DATABASE = 'data.db'

# ============ DATABASE INITIALIZATION ============
def init_db():
    """إنشاء جداول قاعدة البيانات"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # جدول بانيو
    c.execute('''CREATE TABLE IF NOT EXISTS banyo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        problem_number TEXT NOT NULL,
        technician_name TEXT,
        piece_code TEXT,
        quantity INTEGER,
        reason TEXT,
        inspection_date TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول خلاطات
    c.execute('''CREATE TABLE IF NOT EXISTS khallat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        order_number TEXT NOT NULL,
        technician_name TEXT,
        type TEXT,
        code TEXT,
        quantity INTEGER,
        reason TEXT,
        exit_date TEXT,
        group_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول موبيليا
    c.execute('''CREATE TABLE IF NOT EXISTS mobelya (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        problem_number TEXT NOT NULL,
        technician_name TEXT,
        item_description TEXT,
        piece_code TEXT,
        quantity INTEGER,
        unit_code TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول قاعدة البيانات
    c.execute('''CREATE TABLE IF NOT EXISTS database (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        type TEXT NOT NULL,
        type_code TEXT NOT NULL,
        price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول صينى
    c.execute('''CREATE TABLE IF NOT EXISTS sini (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        problem_number TEXT NOT NULL,
        technician_name TEXT,
        item_description TEXT,
        code TEXT,
        quantity INTEGER,
        in_storage TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ============ HELPER FUNCTIONS ============
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """تحويل sqlite3.Row إلى dictionary"""
    return dict(row) if row else None

def rows_to_list(rows):
    """تحويل قائمة rows إلى dictionaries"""
    return [dict(row) for row in rows]

# ============ GENERIC CRUD FUNCTIONS ============
def get_all_records(table):
    """الحصول على جميع السجلات من جدول معين"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f'SELECT * FROM {table} ORDER BY id DESC')
    records = rows_to_list(c.fetchall())
    conn.close()
    return records

def get_record_by_id(table, record_id):
    """الحصول على سجل واحد بواسطة ID"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f'SELECT * FROM {table} WHERE id = ?', (record_id,))
    record = dict_from_row(c.fetchone())
    conn.close()
    return record

def search_records(table, query):
    """البحث في جميع الأعمدة"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # الحصول على أسماء الأعمدة
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall() if col[1] not in ['id', 'created_at', 'updated_at']]
    
    # بناء جملة البحث
    search_conditions = ' OR '.join([f"{col} LIKE ?" for col in columns])
    search_param = [f"%{query}%"] * len(columns)
    
    c.execute(f'SELECT * FROM {table} WHERE {search_conditions} ORDER BY id DESC', search_param)
    records = rows_to_list(c.fetchall())
    conn.close()
    return records

def add_record(table, data):
    """إضافة سجل جديد"""
    conn = get_db_connection()
    c = conn.cursor()
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    values = tuple(data.values())
    
    c.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', values)
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    return record_id

def update_record(table, record_id, data):
    """تحديث سجل موجود"""
    conn = get_db_connection()
    c = conn.cursor()
    
    data['updated_at'] = datetime.now().isoformat()
    
    set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
    values = tuple(data.values()) + (record_id,)
    
    c.execute(f'UPDATE {table} SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

def delete_record(table, record_id):
    """حذف سجل"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f'DELETE FROM {table} WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

# ============ API ENDPOINTS ============

# بانيو
@app.route('/api/banyo', methods=['GET'])
def get_banyo():
    search = request.args.get('search', '').strip()
    if search:
        records = search_records('banyo', search)
    else:
        records = get_all_records('banyo')
    return jsonify(records)

@app.route('/api/banyo/<int:record_id>', methods=['GET'])
def get_banyo_detail(record_id):
    record = get_record_by_id('banyo', record_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/api/banyo', methods=['POST'])
def add_banyo():
    data = request.get_json()
    try:
        record_id = add_record('banyo', data)
        record = get_record_by_id('banyo', record_id)
        return jsonify(record), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/banyo/<int:record_id>', methods=['PUT'])
def update_banyo(record_id):
    data = request.get_json()
    try:
        update_record('banyo', record_id, data)
        record = get_record_by_id('banyo', record_id)
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/banyo/<int:record_id>', methods=['DELETE'])
def delete_banyo(record_id):
    delete_record('banyo', record_id)
    return jsonify({'success': True})

# خلاطات
@app.route('/api/khallat', methods=['GET'])
def get_khallat():
    search = request.args.get('search', '').strip()
    if search:
        records = search_records('khallat', search)
    else:
        records = get_all_records('khallat')
    return jsonify(records)

@app.route('/api/khallat/<int:record_id>', methods=['GET'])
def get_khallat_detail(record_id):
    record = get_record_by_id('khallat', record_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/api/khallat', methods=['POST'])
def add_khallat():
    data = request.get_json()
    try:
        record_id = add_record('khallat', data)
        record = get_record_by_id('khallat', record_id)
        return jsonify(record), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/khallat/<int:record_id>', methods=['PUT'])
def update_khallat(record_id):
    data = request.get_json()
    try:
        update_record('khallat', record_id, data)
        record = get_record_by_id('khallat', record_id)
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/khallat/<int:record_id>', methods=['DELETE'])
def delete_khallat(record_id):
    delete_record('khallat', record_id)
    return jsonify({'success': True})

# موبيليا
@app.route('/api/mobelya', methods=['GET'])
def get_mobelya():
    search = request.args.get('search', '').strip()
    if search:
        records = search_records('mobelya', search)
    else:
        records = get_all_records('mobelya')
    return jsonify(records)

@app.route('/api/mobelya/<int:record_id>', methods=['GET'])
def get_mobelya_detail(record_id):
    record = get_record_by_id('mobelya', record_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/api/mobelya', methods=['POST'])
def add_mobelya():
    data = request.get_json()
    try:
        record_id = add_record('mobelya', data)
        record = get_record_by_id('mobelya', record_id)
        return jsonify(record), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/mobelya/<int:record_id>', methods=['PUT'])
def update_mobelya(record_id):
    data = request.get_json()
    try:
        update_record('mobelya', record_id, data)
        record = get_record_by_id('mobelya', record_id)
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/mobelya/<int:record_id>', methods=['DELETE'])
def delete_mobelya(record_id):
    delete_record('mobelya', record_id)
    return jsonify({'success': True})

# قاعدة البيانات
@app.route('/api/database', methods=['GET'])
def get_database():
    search = request.args.get('search', '').strip()
    if search:
        records = search_records('database', search)
    else:
        records = get_all_records('database')
    return jsonify(records)

@app.route('/api/database/<int:record_id>', methods=['GET'])
def get_database_detail(record_id):
    record = get_record_by_id('database', record_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/api/database', methods=['POST'])
def add_database():
    data = request.get_json()
    try:
        record_id = add_record('database', data)
        record = get_record_by_id('database', record_id)
        return jsonify(record), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/database/<int:record_id>', methods=['PUT'])
def update_database(record_id):
    data = request.get_json()
    try:
        update_record('database', record_id, data)
        record = get_record_by_id('database', record_id)
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/database/<int:record_id>', methods=['DELETE'])
def delete_database(record_id):
    delete_record('database', record_id)
    return jsonify({'success': True})

# صينى
@app.route('/api/sini', methods=['GET'])
def get_sini():
    search = request.args.get('search', '').strip()
    if search:
        records = search_records('sini', search)
    else:
        records = get_all_records('sini')
    return jsonify(records)

@app.route('/api/sini/<int:record_id>', methods=['GET'])
def get_sini_detail(record_id):
    record = get_record_by_id('sini', record_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/api/sini', methods=['POST'])
def add_sini():
    data = request.get_json()
    try:
        record_id = add_record('sini', data)
        record = get_record_by_id('sini', record_id)
        return jsonify(record), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sini/<int:record_id>', methods=['PUT'])
def update_sini(record_id):
    data = request.get_json()
    try:
        update_record('sini', record_id, data)
        record = get_record_by_id('sini', record_id)
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sini/<int:record_id>', methods=['DELETE'])
def delete_sini(record_id):
    delete_record('sini', record_id)
    return jsonify({'success': True})

# ============ EXPORT/BACKUP ============
@app.route('/api/export/<section>', methods=['GET'])
def export_csv(section):
    """تنزيل البيانات كـ CSV"""
    records = get_all_records(section)
    
    if not records:
        return jsonify({'error': 'No data to export'}), 404
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    
    output.seek(0)
    byte_output = BytesIO()
    byte_output.write(output.getvalue().encode('utf-8-sig'))
    byte_output.seek(0)
    
    return send_file(
        byte_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{section}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/backup', methods=['GET'])
def backup_all():
    """Backup كامل البيانات"""
    backup_data = {}
    for section in ['banyo', 'khallat', 'mobelya', 'database', 'sini']:
        backup_data[section] = get_all_records(section)
    
    return jsonify(backup_data)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """إحصائيات عن البيانات"""
    stats = {}
    for section in ['banyo', 'khallat', 'mobelya', 'database', 'sini']:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(f'SELECT COUNT(*) as count FROM {section}')
        count = c.fetchone()['count']
        conn.close()
        stats[section] = count
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
