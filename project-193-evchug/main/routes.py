import os

import uuid
from flask import request, render_template, url_for, send_from_directory, flash
from flask_login import login_user, login_required, logout_user
from flask_login.utils import _get_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename, redirect

from main import db, app, ALLOWED_EXTENSIONS
from models.graffiti import Graffiti
from models.user import User

MAX_FILE_SIZE = 1024 * 1024 + 1


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/add_graffito', methods=['GET', 'POST'])
def upload_graffito():
    if request.method == 'POST':
        file = request.files['file']

        file_type = secure_filename(file.filename).split('.')
        filename = f'{uuid.uuid1()}.{file_type[1]}'

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        address = request.form['address']
        description = request.form['description']

        users_graffito = Graffiti(username=username,
                                  email=email,
                                  address=address,
                                  description=description,
                                  file_name=filename,
                                  name=name)
        try:
            db.session.add(users_graffito)
            db.session.commit()
            return redirect(url_for('graffito_done'))
        except Exception as error:
            return f'При отправке формы произошла ошибка: {str(error)}'
    else:
        return render_template("send_graffito.html", user=_get_user())


@app.route('/graffito_done')
def graffito_done():
    return render_template('graffito_done.html', user=_get_user())


@app.route('/<filename>')
def favicon(filename):
    return send_from_directory(os.path.abspath("main/templates/static"), filename)


@app.route('/')
def main():
    return render_template('main.html', user=_get_user())


@app.route('/map')
def map():
    return render_template('map.html', user=_get_user())


@app.route('/base')
def all_graffiti():
    graffiti = Graffiti.query.order_by(Graffiti.id).filter(Graffiti.active == True).all()
    for i in graffiti:
        i.file_name = f"/graffiti/{i.file_name}"
        i.added = f'{i.added.year}-{i.added.month}-{i.added.day}'

    return render_template('all_graffiti.html', graffiti=graffiti, user=_get_user())


@app.route('/graffiti/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/graffito/<id>')
def graffito(id):
    graffiti = Graffiti.query.filter_by(id=id).first()
    graffiti.file_name = f"/graffiti/{graffiti.file_name}"
    graffiti.added = f'{graffiti.added.year}-{graffiti.added.month}-{graffiti.added.day}'
    return render_template('graffito.html', graffiti=graffiti, user=_get_user())


@app.route('/graffito/<id>/edit', methods=['GET', 'POST'])
@login_required
def graffito_edit(id):
    graffiti = Graffiti.query.get_or_404(id)
    if request.method == 'POST':

        graffiti.name = request.form['name']
        graffiti.address = request.form['address']
        graffiti.description = request.form['description']

        try:
            db.session.commit()
            return redirect('/admin')
        except Exception as error:
            return f'При редактировании олбьекта произошла ошибка: {str(error)}'

    else:
        graffiti.file_name = f"/graffiti/{graffiti.file_name}"
        graffiti.added = f'{graffiti.added.year}-{graffiti.added.month}-{graffiti.added.day}'
        graffiti.name = f'{graffiti.name}'
        return render_template('graffito_edit.html', graffiti=graffiti, user=_get_user())


@app.route('/graffito/<id>/sucsess', methods=['GET'])
@login_required
def graffito_sucsess(id):
    graffiti = Graffiti.query.get_or_404(id)
    graffiti.active = True
    try:
        db.session.commit()
        return redirect('/admin')
    except Exception as error:
        return f'При редактировании олбьекта произошла ошибка: {str(error)}'


@app.route('/graffito/<id>/delete', methods=['GET'])
@login_required
def graffito_del(id):
    graffiti = Graffiti.query.get_or_404(id)
    try:
        db.session.delete(graffiti)
        db.session.commit()
        return redirect('/admin')
    except Exception as error:
        return f'При редактировании олбьекта произошла ошибка: {str(error)}'


@app.route('/admin/')
@login_required
def admin():
    graffiti = Graffiti.query.order_by(Graffiti.id).filter(Graffiti.active == False).all()
    for i in graffiti:
        i.file_name = f"/graffiti/{i.file_name}"
        i.added = f'{i.added.year}-{i.added.month}-{i.added.day}'

    return render_template('admin.html', graffiti=graffiti, user=_get_user())


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    user = User.query.filter_by(login=login).first()

    if user and check_password_hash(user.password, password):
        login_user(user)

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        else:
            return redirect(url_for('all_graffiti'))
    else:
        flash('Неверный логин или пароль')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    code = request.form.get('code')

    if request.method == 'POST':
        if password != password2:
            flash('Пароли не совпадают')
        elif code != 'qwerty':
            flash('Неверный код для регистрации')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))

    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('all_graffiti'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)

    return response
