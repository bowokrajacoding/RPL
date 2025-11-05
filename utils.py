import os
import time
from flask import current_app, render_template
from werkzeug.utils import secure_filename
from xhtml2pdf import pisa

ALLOWED_EXT = set(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def save_upload(file_storage):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    path = os.path.join(upload_folder, filename)
    file_storage.save(path)
    return filename


def generate_pdf_from_template(template_name, context, output_filename):
    """Generate PDF file from HTML template using xhtml2pdf."""
    html = render_template(template_name, **context)
    upload_folder = current_app.config['UPLOAD_FOLDER']

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    out_path = os.path.join(upload_folder, output_filename)

    with open(out_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        raise Exception("Gagal membuat PDF")

    # Simpan hanya nama file, bukan path lengkap
    return output_filename

