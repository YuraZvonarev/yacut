from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, URL, Optional


class MainUrlForm(FlaskForm):
    original_link = StringField(
        'Длинная ссылка',
        validators=[
            DataRequired('Обязательное поле'),
            URL(message='Введите URL')
        ]
    )
    custom_id = StringField(
        'Короткая ссылка',
        validators=[
            Length(max=16, message='Не больше 16 символов'),
            Optional()
        ]
    )
    submit = SubmitField('Сократить')


class FileForm(FlaskForm):
    files = MultipleFileField(
        'ВЫберите файлы',
        validators=[
            DataRequired(message='Выберите хотя бы один файл')
        ]
    )
    submit = SubmitField('Загрузить')