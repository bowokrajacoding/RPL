from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    jabatan = db.Column(db.String(150))
    nip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class IncomingMail(db.Model):
    __tablename__ = 'incoming_mail'
    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(120), nullable=False)
    asal = db.Column(db.String(200))
    perihal = db.Column(db.String(300))
    tanggal_diterima = db.Column(db.Date)
    file_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OutgoingMail(db.Model):
    __tablename__ = 'outgoing_mail'
    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(120))
    perihal = db.Column(db.String(300))
    tanggal = db.Column(db.Date)
    tujuan = db.Column(db.String(200))
    isi = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # link to Employees for assignment (many-to-many optionally)
    assigned_to = db.Column(db.String(300))  # comma-separated employee ids (simple)
    pdf_path = db.Column(db.String(300))
