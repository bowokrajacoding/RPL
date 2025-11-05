from app import create_app
from models import db, User
from getpass import getpass

app = create_app()

with app.app_context():
    db.create_all()
    # create initial admin if not exist
    if not User.query.filter_by(username='admin').first():
        pw = 'admin123'
        # optional: input from console
        # pw = getpass('Password for initial admin: ')
        admin = User(username='admin', full_name='Admin', is_admin=True)
        admin.set_password(pw)
        db.session.add(admin)
        db.session.commit()
        print('Created admin with username=admin and password=admin123 (please change!)')
    else:
        print('admin exists')
