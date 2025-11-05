import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from config import Config
from models import db, User, Employee, IncomingMail, OutgoingMail
from forms import LoginForm, EmployeeForm, IncomingMailForm, OutgoingMailForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from utils import save_upload, allowed_file, generate_pdf_from_template
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET','POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Username atau password salah', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_pegawai = Employee.query.count()
        total_masuk = IncomingMail.query.count()
        total_keluar = OutgoingMail.query.count()
        return render_template('dashboard.html', total_pegawai=total_pegawai, total_masuk=total_masuk, total_keluar=total_keluar)

    # --- Pegawai CRUD ---
    @app.route('/pegawai')
    @login_required
    def pegawai_list():
        q = request.args.get('q','')
        if q:
            pegawais = Employee.query.filter(Employee.nama.ilike(f'%{q}%')).all()
        else:
            pegawais = Employee.query.all()
        return render_template('pegawai_list.html', pegawais=pegawais, q=q)

    @app.route('/pegawai/add', methods=['GET','POST'])
    @login_required
    def pegawai_add():
        form = EmployeeForm()
        if form.validate_on_submit():
            e = Employee(nama=form.nama.data, jabatan=form.jabatan.data, nip=form.nip.data)
            db.session.add(e)
            db.session.commit()
            flash('Pegawai ditambahkan', 'success')
            return redirect(url_for('pegawai_list'))
        return render_template('pegawai_form.html', form=form)

    # --- Surat Masuk ---
    @app.route('/surat-masuk')
    @login_required
    def surat_masuk_list():
        q = request.args.get('q','')
        if q:
            ms = IncomingMail.query.filter(
                (IncomingMail.nomor.ilike(f'%{q}%')) |
                (IncomingMail.perihal.ilike(f'%{q}%'))
            ).all()
        else:
            ms = IncomingMail.query.order_by(IncomingMail.tanggal_diterima.desc()).all()
        return render_template('surat_masuk_list.html', mails=ms, q=q)

    @app.route('/surat-masuk/add', methods=['GET','POST'])
    @login_required
    def surat_masuk_add():
        form = IncomingMailForm()
        if form.validate_on_submit():
            file_path = None
            f = request.files.get('file')
            if f and allowed_file(f.filename):
                file_path = save_upload(f)
            mail = IncomingMail(
                nomor=form.nomor.data,
                asal=form.asal.data,
                perihal=form.perihal.data,
                tanggal_diterima=form.tanggal_diterima.data,
                file_path=file_path
            )
            db.session.add(mail)
            db.session.commit()
            flash('Surat masuk disimpan', 'success')
            return redirect(url_for('surat_masuk_list'))
        return render_template('surat_masuk_form.html', form=form)

    # --- Surat Keluar ---
    @app.route('/surat-keluar')
    @login_required
    def surat_keluar_list():
        q = request.args.get('q','')
        if q:
            ms = OutgoingMail.query.filter(
                (OutgoingMail.nomor.ilike(f'%{q}%')) |
                (OutgoingMail.perihal.ilike(f'%{q}%'))
            ).all()
        else:
            ms = OutgoingMail.query.order_by(OutgoingMail.tanggal.desc()).all()
        return render_template('surat_keluar_list.html', mails=ms, q=q)

    @app.route('/surat-keluar/add', methods=['GET','POST'])
    @login_required
    def surat_keluar_add():
        form = OutgoingMailForm()
        # set choices for assigned_to
        all_emps = Employee.query.all()
        form.assigned_to.choices = [(e.id, f"{e.nama} ({e.jabatan})") for e in all_emps]

        if form.validate_on_submit():
            assigned_ids = ','.join([str(x) for x in form.assigned_to.data]) if form.assigned_to.data else ''
            mail = OutgoingMail(
                nomor=form.nomor.data,
                perihal=form.perihal.data,
                tanggal=form.tanggal.data,
                tujuan=form.tujuan.data,
                isi=form.isi.data,
                assigned_to=assigned_ids,
                created_by=current_user.id
            )
            db.session.add(mail)
            db.session.commit()
            # generate PDF
            # prepare employee names
            assigned_names = []
            if assigned_ids:
                ids = [int(i) for i in assigned_ids.split(',')]
                emps = Employee.query.filter(Employee.id.in_(ids)).all()
                assigned_names = [e.nama for e in emps]
            context = {
                'kop_title': 'DINAS KESEHATAN BLUD PUSKESMAS KUTARAYA',
                'nomor': mail.nomor,
                'perihal': mail.perihal,
                'tanggal': mail.tanggal.strftime('%Y-%m-%d') if mail.tanggal else '',
                'tujuan': mail.tujuan,
                'isi': mail.isi,
                'assigned_names': assigned_names
            }
            out_filename = f"surat_keluar_{mail.id}.pdf"
            try:
                pdf_path = generate_pdf_from_template('surat_keluar_template.html', context, out_filename)
                mail.pdf_path = pdf_path
                db.session.commit()
            except Exception as e:
                flash(f'PDF generation failed: {e}', 'warning')

            flash('Surat keluar dibuat', 'success')
            return redirect(url_for('surat_keluar_list'))

        return render_template('surat_keluar_form.html', form=form)

    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/arsip')
    @login_required
    def arsip_list():
        # combine incoming and outgoing maybe paginated
        q = request.args.get('q','')
        incoming = IncomingMail.query
        outgoing = OutgoingMail.query
        if q:
            incoming = incoming.filter((IncomingMail.nomor.ilike(f'%{q}%')) | (IncomingMail.perihal.ilike(f'%{q}%')))
            outgoing = outgoing.filter((OutgoingMail.nomor.ilike(f'%{q}%')) | (OutgoingMail.perihal.ilike(f'%{q}%')))
        incoming = incoming.all()
        outgoing = outgoing.all()
        return render_template('arsip_list.html', incoming=incoming, outgoing=outgoing, q=q)


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from config import Config
from models import db, User, Employee, IncomingMail, OutgoingMail
from forms import LoginForm, EmployeeForm, IncomingMailForm, OutgoingMailForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from utils import save_upload, allowed_file, generate_pdf_from_template
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET','POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Username atau password salah', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_pegawai = Employee.query.count()
        total_masuk = IncomingMail.query.count()
        total_keluar = OutgoingMail.query.count()
        return render_template('dashboard.html', total_pegawai=total_pegawai, total_masuk=total_masuk, total_keluar=total_keluar)

    # --- Pegawai CRUD ---
    @app.route('/pegawai')
    @login_required
    def pegawai_list():
        q = request.args.get('q','')
        if q:
            pegawais = Employee.query.filter(Employee.nama.ilike(f'%{q}%')).all()
        else:
            pegawais = Employee.query.all()
        return render_template('pegawai_list.html', pegawais=pegawais, q=q)

    @app.route('/pegawai/add', methods=['GET','POST'])
    @login_required
    def pegawai_add():
        form = EmployeeForm()
        if form.validate_on_submit():
            e = Employee(nama=form.nama.data, jabatan=form.jabatan.data, nip=form.nip.data)
            db.session.add(e)
            db.session.commit()
            flash('Pegawai ditambahkan', 'success')
            return redirect(url_for('pegawai_list'))
        return render_template('pegawai_form.html', form=form)

    # --- Surat Masuk ---
    @app.route('/surat-masuk')
    @login_required
    def surat_masuk_list():
        q = request.args.get('q','')
        if q:
            ms = IncomingMail.query.filter(
                (IncomingMail.nomor.ilike(f'%{q}%')) |
                (IncomingMail.perihal.ilike(f'%{q}%'))
            ).all()
        else:
            ms = IncomingMail.query.order_by(IncomingMail.tanggal_diterima.desc()).all()
        return render_template('surat_masuk_list.html', mails=ms, q=q)

    @app.route('/surat-masuk/add', methods=['GET','POST'])
    @login_required
    def surat_masuk_add():
        form = IncomingMailForm()
        if form.validate_on_submit():
            file_path = None
            f = request.files.get('file')
            if f and allowed_file(f.filename):
                file_path = save_upload(f)
            mail = IncomingMail(
                nomor=form.nomor.data,
                asal=form.asal.data,
                perihal=form.perihal.data,
                tanggal_diterima=form.tanggal_diterima.data,
                file_path=file_path
            )
            db.session.add(mail)
            db.session.commit()
            flash('Surat masuk disimpan', 'success')
            return redirect(url_for('surat_masuk_list'))
        return render_template('surat_masuk_form.html', form=form)

    # --- Surat Keluar ---
    @app.route('/surat-keluar')
    @login_required
    def surat_keluar_list():
        q = request.args.get('q','')
        if q:
            ms = OutgoingMail.query.filter(
                (OutgoingMail.nomor.ilike(f'%{q}%')) |
                (OutgoingMail.perihal.ilike(f'%{q}%'))
            ).all()
        else:
            ms = OutgoingMail.query.order_by(OutgoingMail.tanggal.desc()).all()
        return render_template('surat_keluar_list.html', mails=ms, q=q)

    @app.route('/surat-keluar/add', methods=['GET','POST'])
    @login_required
    def surat_keluar_add():
        form = OutgoingMailForm()
        # set choices for assigned_to
        all_emps = Employee.query.all()
        form.assigned_to.choices = [(e.id, f"{e.nama} ({e.jabatan})") for e in all_emps]

        if form.validate_on_submit():
            assigned_ids = ','.join([str(x) for x in form.assigned_to.data]) if form.assigned_to.data else ''
            mail = OutgoingMail(
                nomor=form.nomor.data,
                perihal=form.perihal.data,
                tanggal=form.tanggal.data,
                tujuan=form.tujuan.data,
                isi=form.isi.data,
                assigned_to=assigned_ids,
                created_by=current_user.id
            )
            db.session.add(mail)
            db.session.commit()
            # generate PDF
            # prepare employee names
            assigned_names = []
            if assigned_ids:
                ids = [int(i) for i in assigned_ids.split(',')]
                emps = Employee.query.filter(Employee.id.in_(ids)).all()
                assigned_names = [e.nama for e in emps]
            context = {
                'kop_title': 'DINAS KESEHATAN BLUD PUSKESMAS KUTARAYA',
                'nomor': mail.nomor,
                'perihal': mail.perihal,
                'tanggal': mail.tanggal.strftime('%Y-%m-%d') if mail.tanggal else '',
                'tujuan': mail.tujuan,
                'isi': mail.isi,
                'assigned_names': assigned_names
            }
            out_filename = f"surat_keluar_{mail.id}.pdf"
            try:
                pdf_path = generate_pdf_from_template('surat_keluar_template.html', context, out_filename)
                mail.pdf_path = pdf_path
                db.session.commit()
            except Exception as e:
                flash(f'PDF generation failed: {e}', 'warning')

            flash('Surat keluar dibuat', 'success')
            return redirect(url_for('surat_keluar_list'))

        return render_template('surat_keluar_form.html', form=form)

    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/arsip')
    @login_required
    def arsip_list():
        # combine incoming and outgoing maybe paginated
        q = request.args.get('q','')
        incoming = IncomingMail.query
        outgoing = OutgoingMail.query
        if q:
            incoming = incoming.filter((IncomingMail.nomor.ilike(f'%{q}%')) | (IncomingMail.perihal.ilike(f'%{q}%')))
            outgoing = outgoing.filter((OutgoingMail.nomor.ilike(f'%{q}%')) | (OutgoingMail.perihal.ilike(f'%{q}%')))
        incoming = incoming.all()
        outgoing = outgoing.all()
        return render_template('arsip_list.html', incoming=incoming, outgoing=outgoing, q=q)


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
