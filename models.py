from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    joining_date = db.Column(db.Date, nullable=False, default=lambda: date.today())
    salary = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)