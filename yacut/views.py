from flask import render_template, request, redirect, url_for, flash
from . import app, db
from .models import URLMap
from .forms import MainUrlForm, FileForm
import random
import asyncio
import aiohttp
from . import app


def generate_short_id():
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    result = ''
    for _ in range(6):
        result += random.choice(chars)
    return result


def get_unique_short_id():
    while True:
        short = generate_short_id()
        if not URLMap.query.filter_by(short=short).first():
            return short


@app.route('/', methods=['GET', 'POST'])
def index():
    form = MainUrlForm()
    short_url = None
    if form.validate_on_submit():
        original = form.original_link.data
        custom = form.custom_id.data
        if custom:
            if custom == 'files':
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)
            if URLMap.query.filter_by(short=custom).first():
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)
            short_id = custom
        else:
            short_id = get_unique_short_id()
        db.session.add(URLMap(original=original, short=short_id))
        db.session.commit()
        short_url = request.host_url + short_id
    return render_template('index.html', form=form, short_url=short_url)


@app.route('/<short_id>')
def redirect_to_original(short_id):
    link = URLMap.query.filter_by(short=short_id).first_or_404()
    return redirect(link.original)


async def upload_one_file(session, file, token):
    headers = {'Authorization': f'OAuth {token}'}
    async with session.get(
        'https://cloud-api.yandex.net/v1/disk/resources/upload',
        headers=headers,
        params={'path': f'app:/{file.filename}', 'overwrite': 'true'}
    ) as response:
        data = await response.json()
        upload_url = data['href']

    async with session.put(upload_url, data=file.read()) as response:
        pass

    async with session.get(
        'https://cloud-api.yandex.net/v1/disk/resources/download',
        headers=headers,
        params={'path': f'app:/{file.filename}'}
    ) as response:
        data = await response.json()
        return data['href']


async def async_upload_files(files, token):
    async with aiohttp.ClientSession() as session:
        tasks = [upload_one_file(session, file, token) for file in files]
        return await asyncio.gather(*tasks)


@app.route('/files', methods=['GET', 'POST'])
def upload_files():
    form = FileForm()
    saved_files = []
    if form.validate_on_submit():
        files = form.files.data
        token = app.config['DISK_TOKEN']
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        download_links = loop.run_until_complete(
            async_upload_files(files, token))
        loop.close()
        for file, link in zip(files, download_links):
            short_id = get_unique_short_id()
            url_map = URLMap(original=link, short=short_id)
            db.session.add(url_map)
            db.session.commit()
            saved_files.append({
                'name': file.filename,
                'link': request.host_url + short_id
            })
        flash(f'Загружено {len(saved_files)} файлов на Яндекс Диск')
    return render_template('files.html', form=form, saved_files=saved_files)