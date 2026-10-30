"""SQLite persistence for student records and prediction history."""
import sqlite3, json
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'data'/'student_risk.db'
def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB_PATH,check_same_thread=False); con.row_factory=sqlite3.Row; return con

def init_db():
    with connect() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS students(student_id TEXT PRIMARY KEY, student_name TEXT NOT NULL, age INTEGER, gender TEXT, attendance_pct REAL, previous_gpa REAL, internal_marks_pct REAL, assignment_completion_pct REAL, backlogs INTEGER, study_hours_per_day REAL, previous_failures INTEGER, class_participation_pct REAL, assignment_submission_rate REAL, number_of_subjects INTEGER, previous_semester_pct REAL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, risk_level TEXT NOT NULL, risk_probability REAL NOT NULL, probabilities_json TEXT, reasons_json TEXT, recommendations_json TEXT, model_name TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(student_id) REFERENCES students(student_id));
        CREATE TABLE IF NOT EXISTS model_metrics(model_name TEXT PRIMARY KEY, accuracy REAL, precision REAL, recall REAL, f1 REAL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);""")

def save_student(s):
    keys=['student_id','student_name','age','gender','attendance_pct','previous_gpa','internal_marks_pct','assignment_completion_pct','backlogs','study_hours_per_day','previous_failures','class_participation_pct','assignment_submission_rate','number_of_subjects','previous_semester_pct']
    vals=[s.get(k) for k in keys]
    with connect() as c: c.execute(f"INSERT INTO students({','.join(keys)}) VALUES({','.join(['?']*len(keys))}) ON CONFLICT(student_id) DO UPDATE SET "+','.join(f'{k}=excluded.{k}' for k in keys[1:])+", updated_at=CURRENT_TIMESTAMP",vals)


def save_student_and_prediction(student, result):
    """Atomically upsert a student record and append a prediction history row."""
    keys = [
        'student_id', 'student_name', 'age', 'gender', 'attendance_pct',
        'previous_gpa', 'internal_marks_pct', 'assignment_completion_pct',
        'backlogs', 'study_hours_per_day', 'previous_failures',
        'class_participation_pct', 'assignment_submission_rate',
        'number_of_subjects', 'previous_semester_pct'
    ]
    # Convert pandas/NumPy scalar values to native Python types for sqlite3.
    values = []
    for key in keys:
        value = student.get(key)
        if hasattr(value, 'item'):
            value = value.item()
        values.append(value)
    with connect() as con:
        con.execute(
            f"INSERT INTO students({','.join(keys)}) VALUES({','.join(['?'] * len(keys))}) "
            "ON CONFLICT(student_id) DO UPDATE SET "
            + ','.join(f'{key}=excluded.{key}' for key in keys[1:])
            + ', updated_at=CURRENT_TIMESTAMP',
            values,
        )
        con.execute(
            "INSERT INTO predictions(student_id, risk_level, risk_probability, probabilities_json, reasons_json, recommendations_json, model_name) VALUES(?,?,?,?,?,?,?)",
            (
                student['student_id'], result['risk_level'], result['risk_probability'],
                json.dumps(result['probabilities']), json.dumps(result['reasons']),
                json.dumps(result['recommendations']), result['model_name'],
            ),
        )

def get_students():
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM students ORDER BY student_id').fetchall()]
def delete_student(student_id):
    with connect() as c: c.execute('DELETE FROM predictions WHERE student_id=?',(student_id,)); c.execute('DELETE FROM students WHERE student_id=?',(student_id,))
def save_prediction(student_id, result):
    with connect() as c: c.execute('INSERT INTO predictions(student_id,risk_level,risk_probability,probabilities_json,reasons_json,recommendations_json,model_name) VALUES(?,?,?,?,?,?,?)',(student_id,result['risk_level'],result['risk_probability'],json.dumps(result['probabilities']),json.dumps(result['reasons']),json.dumps(result['recommendations']),result['model_name']))
def get_predictions(student_id=None):
    with connect() as c:
        if student_id: rows=c.execute('SELECT * FROM predictions WHERE student_id=? ORDER BY created_at DESC, id DESC',(student_id,)).fetchall()
        else: rows=c.execute('SELECT p.*,s.student_name FROM predictions p LEFT JOIN students s USING(student_id) ORDER BY created_at DESC, id DESC').fetchall()
        return [dict(r) for r in rows]
def save_metrics(rows):
    with connect() as c:
        for r in rows: c.execute('INSERT OR REPLACE INTO model_metrics(model_name,accuracy,precision,recall,f1) VALUES(?,?,?,?,?)',(r['model'],r['accuracy'],r['precision'],r['recall'],r['f1']))
def get_metrics():
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM model_metrics ORDER BY f1 DESC').fetchall()]