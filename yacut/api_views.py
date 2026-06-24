from flask import jsonify, request
from . import app, db
from .models import URLMap
from .views import get_unique_short_id
import re


@app.route('/api/id/', methods=['POST'])
def create_short_link():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"message": "Отсутствует тело запроса"}), 400
    if 'url' not in data:
        return jsonify({"message": '"url" является обязательным полем!'}), 400
    original = data['url']
    custom = data.get('custom_id')
    if custom:
        if len(custom) > 16:
            return jsonify({
                "message": 'Указано недопустимое имя для короткой ссылки'
            }), 400
        if not re.match(r'^[A-Za-z0-9]+$', custom):
            return jsonify({
                "message": 'Указано недопустимое имя для короткой ссылки'
            }), 400
        if custom == 'files':
            return jsonify({"message": 'Недопустимый идентификатор'}), 400
        if URLMap.query.filter_by(short=custom).first():
            return jsonify({
                "message":
                'Предложенный вариант короткой ссылки уже существует.'
            }), 400
        short_id = custom
    else:
        short_id = get_unique_short_id()
    link = URLMap(original=original, short=short_id)
    db.session.add(link)
    db.session.commit()
    return jsonify({
        'short_link': request.host_url + short_id,
        'url': original
    }), 201


@app.route('/api/id/<short_id>/', methods=['GET'])
def get_original_link(short_id):
    link = URLMap.query.filter_by(short=short_id).first()
    if not link:
        return jsonify({"message": 'Указанный id не найден'}), 404
    return jsonify({'url': link.original}), 200