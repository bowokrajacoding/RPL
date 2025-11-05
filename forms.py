from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectMultipleField, DateField, FileField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EmployeeForm(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired(), Length(max=150)])
    jabatan = StringField('Jabatan')
    nip = StringField('NIP')
    submit = SubmitField('Simpan')

class IncomingMailForm(FlaskForm):
    nomor = StringField('Nomor Surat', validators=[DataRequired()])
    asal = StringField('Asal Surat')
    perihal = StringField('Perihal')
    tanggal_diterima = DateField('Tanggal Diterima', format='%Y-%m-%d')
    file = FileField('Lampiran')
    submit = SubmitField('Simpan')

class OutgoingMailForm(FlaskForm):
    nomor = StringField('Nomor Surat')
    perihal = StringField('Perihal', validators=[DataRequired()])
    tanggal = DateField('Tanggal Surat', format='%Y-%m-%d')
    tujuan = StringField('Tujuan')
    isi = TextAreaField('Isi Surat', validators=[DataRequired()])
    assigned_to = SelectMultipleField('Pegawai yang Ditugaskan', coerce=int)
    submit = SubmitField('Buat & Simpan')
