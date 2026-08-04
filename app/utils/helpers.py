import os
import io
import uuid
from datetime import date, timedelta, datetime
from PIL import Image
from flask import current_app
from app import db


def save_profile_picture(form_picture):
    from app.models_ext import UploadedImage
    img = Image.open(form_picture)
    img.thumbnail((300, 300))
    buf = io.BytesIO()
    filename = (form_picture.filename or '').lower()
    fmt = 'PNG' if filename.endswith('.png') else 'JPEG'
    if fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    img.save(buf, format=fmt)
    token = uuid.uuid4().hex
    row = UploadedImage(
        token=token,
        data=buf.getvalue(),
        mimetype='image/png' if fmt == 'PNG' else 'image/jpeg'
    )
    db.session.add(row)
    return token


def save_announcement_image(form_image):
    from app.models_ext import UploadedImage
    img = Image.open(form_image)
    img.thumbnail((1200, 1200))
    buf = io.BytesIO()
    filename = (form_image.filename or '').lower()
    fmt = 'PNG' if filename.endswith('.png') else 'JPEG'
    if fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    img.save(buf, format=fmt)
    token = uuid.uuid4().hex
    row = UploadedImage(
        token=token,
        data=buf.getvalue(),
        mimetype='image/png' if fmt == 'PNG' else 'image/jpeg'
    )
    db.session.add(row)
    return token


def delete_file(filename, subdir='uploads'):
    # 'filename' is a DB token (or a token with a category prefix). Delete the stored row.
    if not filename:
        return
    from app.models_ext import UploadedImage
    token = filename.split('/')[-1]
    row = UploadedImage.query.filter_by(token=token).first()
    if row:
        db.session.delete(row)
        db.session.commit()


def generate_member_id():
    import random
    year = date.today().year
    random_num = random.randint(1000, 9999)
    return f'CH-{year}-{random_num}'


def get_date_range(period):
    today = date.today()
    if period == 'today':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'month':
        start = today.replace(day=1)
        return start, today
    elif period == 'year':
        start = today.replace(month=1, day=1)
        return start, today
    else:
        return None, None
