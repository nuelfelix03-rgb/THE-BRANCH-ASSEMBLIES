import os
import uuid
from datetime import date, timedelta, datetime
from PIL import Image
from flask import current_app


def save_profile_picture(form_picture):
    random_filename = uuid.uuid4().hex
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_filename + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'uploads', picture_filename)

    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_filename


def save_announcement_image(form_image):
    random_filename = uuid.uuid4().hex
    _, f_ext = os.path.splitext(form_image.filename)
    image_filename = random_filename + f_ext
    image_path = os.path.join(current_app.root_path, 'static', 'announcement_images', image_filename)

    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    img = Image.open(form_image)
    img.thumbnail((1200, 1200))
    img.save(image_path)

    return image_filename


def delete_file(filename, subdir='uploads'):
    if not filename:
        return
    path = os.path.join(current_app.root_path, 'static', subdir, filename)
    if os.path.exists(path):
        os.remove(path)


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
