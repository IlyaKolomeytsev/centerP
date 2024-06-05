import base64

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_from_directory, send_file, flash
import sqlite3
import hashlib
import io
import os
from PyPDF2 import PdfReader

conn = sqlite3.connect('SearchWork.db')
c = conn.cursor()


conn.commit()
conn.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def connect_db():
    return sqlite3.connect('SearchWork.db')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.pop('username', None)  # Удаляем имя пользователя из сессии
        return redirect(url_for('menu'))


@app.route('/', methods=['GET', 'POST'])
def menu():
    return render_template('menu.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
        else:
            return redirect(url_for('admin'))

    if not session.get('admin_logged_in'):
        return render_template('admin_login.html')

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, active, fullDesc, review, organization, paySystem, workPlaces, education, responsibilities, additionally, workTime FROM work WHERE status = 'pending'")
    ads = cursor.fetchall()
    conn.close()

    ads_dict = []
    for ad in ads:
        ads_dict.append({
            'id': ad[0],
            'name': ad[1],
            'description': ad[2],
            'active': ad[3],
            'fullDesc': ad[4],
            'review': ad[5],
            'organization': ad[6],
            'paySystem': ad[7],
            'workPlaces': ad[8],
            'education': ad[9],
            'responsibilities': ad[10],
            'additionally': ad[11],
            'workTime': ad[12]
        })

    return render_template('admin.html', ads=ads_dict)


@app.route('/admin/approve/<int:id>', methods=['POST'])
def approve_ad(id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False})

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE work SET status = 'approved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/reject/<int:id>', methods=['POST'])
def reject_ad(id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False})

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM work WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_panel'))

@app.route('/show_responses')
def show_responses():
    # Замените на реальную логику получения откликов
    if 'username' in session:
        username = session['username']
        connection = sqlite3.connect('SearchWork.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM registration WHERE username=?', (username,))
        user = cursor.fetchone()

        cursor.execute('SELECT resume FROM registration WHERE username=?', (username,))
        resume_data = cursor.fetchone()

        cursor.execute('SELECT * FROM work WHERE workAdder=?', (username,))
        vacancies = cursor.fetchall()

        cursor.execute('SELECT * FROM otclick WHERE main=?', (username,))
        responses = cursor.fetchall()

        for i, response in enumerate(responses):
            cursor.execute('SELECT last_name FROM registration WHERE username=?', (response[0],))
            user_data = cursor.fetchone()
            if user_data:
                last_name = user_data[0]
                responses[i] = (*response[:-1], last_name)

        connection.close()

        if user:
            is_employer = bool(user[11])

            # Передаем переменные в шаблон
            return render_template('responses.html', user=user, is_employer=is_employer, resume_data=resume_data, vacancies=vacancies, responses=responses)
        else:
            return "Пользователь не найден"
    else:
        return redirect(url_for('login_page'))

@app.route('/summary', methods=['GET'])
def summary():
    if 'username' in session:
        # Получаем данные пользователя для отображения на странице
        username = session['username']
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT last_name, first_name, patronymic, birth_date FROM registration WHERE username=?',
            (username,))
        user = cursor.fetchone()
        connection.close()

        return render_template('summary.html', user=user)
    else:
        return redirect(url_for('login_page'))


@app.route('/submit_Lk', methods=['POST'])
def submit_Lk():
        return redirect(url_for('show_Lk'))

@app.route('/submit_reg', methods=['POST'])
def submit_reg():
        return redirect(url_for('show_reg'))

@app.route('/search_work', methods=['POST'])
def search_work():
        return redirect(url_for('show_work'))

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')


@app.route('/search_worked')
def search_worked():
    if 'username' in session:
        employer_username = session['username']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT last_name, first_name, patronymic, username, phone FROM registration")
        all_users = cursor.fetchall()

        users_with_resume = []

        for user in all_users:
            last_name, first_name, patronymic, username, phone = user
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}.pdf")
            if os.path.exists(resume_path):
                pdf_text = extract_text_from_pdf(resume_path)
                resume_info = extract_resume_info(pdf_text)
                users_with_resume.append((last_name, first_name, patronymic, username, phone, resume_info))

        conn.close()

        return render_template('searchWorked.html', users=users_with_resume, employer_username=employer_username)
    else:
        return redirect(url_for('login_page'))

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_resume_info(pdf_text):
    # Разделение текста на строки
    lines = pdf_text.split('\n')
    # Извлечение строк с 6 по 9 (индексы 5, 6, 7, 8)
    lines_6_to_9 = lines[4:8]
    # Извлечение строк с 20 по 25 (индексы 19, 20, 21, 22, 23, 24)
    lines_20_to_25 = lines[35:40]
    # Объединение выбранных строк обратно в текст с HTML-разделителем
    selected_text = '\n'.join(lines_6_to_9) + '\n' + '\n'.join(lines_20_to_25)
    return selected_text




@app.route('/download_resume', defaults={'username': None})
@app.route('/download_resume/<username>')
def download_resume(username):
    if username is None:
        # Если имя пользователя не указано в URL, возможно, мы вызвали функцию напрямую.
        # В этом случае мы можем вернуть сообщение об ошибке или перенаправить куда-то ещё.
        return "Ошибка: имя пользователя не указано"

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}.pdf")
    if os.path.exists(resume_path):
        return send_file(resume_path, as_attachment=True, attachment_filename=f"{username}.pdf")
    else:
        return "Резюме не найдено"

@app.route('/download_res')
def download_res():
    if 'username' in session:
        username = session['username']
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}.pdf")
        if os.path.exists(resume_path):
            return send_file(resume_path, as_attachment=True, attachment_filename=f"{username}.pdf")
        else:
            return "Резюме не найдено"
    else:
        return "Ошибка: пользователь не аутентифицирован"

@app.route('/download_response/<username>')
def download_response(username):
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}.pdf")
        if os.path.exists(resume_path):
            return send_file(resume_path, as_attachment=True, attachment_filename=f"{username}.pdf")
        else:
            return "Резюме не найдено"


@app.route('/submit_registration', methods=['POST'])
def submit_registration():
    if request.method == 'POST':
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        patronymic = request.form['patronymic']
        birth_date = request.form['birth_date']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']

        # Хэширование пароля
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = connect_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO registration (last_name, first_name, patronymic, birth_date, phone, username, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (last_name, first_name, patronymic, birth_date, phone, username, hashed_password))
        conn.commit()
        conn.close()

        return redirect(url_for('login_page'))  # Перенаправляем на страницу входа после успешной регистрации

    return redirect(url_for('show_reg'))



@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Хэширование введенного пароля
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = connect_db()
        c = conn.cursor()

        # Получение хешированного пароля из базы данных для данного пользователя
        c.execute("SELECT password FROM registration WHERE username=?", (username,))
        result = c.fetchone()

        if result is not None:
            db_password = result[0]
            if hashed_password == db_password:
                # Если хеши совпадают, то аутентификация успешна
                session['username'] = username  # Сохраняем имя пользователя в сессии
                # Проверяем, есть ли сохраненный URL для перенаправления
                if 'redirect_url' in session:
                    redirect_url = session['redirect_url']
                    session.pop('redirect_url', None)  # Очищаем сохраненный URL из сессии
                    return redirect(redirect_url)  # Перенаправляем на сохраненный URL
                else:
                    return redirect(url_for('menu'))  # Если нет сохраненного URL, перенаправляем на главную страницу

        # Если хеши не совпадают или пользователя не существует, перенаправляем на страницу входа с сообщением об ошибке
        return render_template('entrance.html', error_message="Неверный логин или пароль")


@app.route('/check_auth')
def check_auth():
    if 'username' in session:
        # Если пользователь авторизован, возвращаем JSON с информацией об этом
        return jsonify(authenticated=True)
    else:
        # Если пользователь не авторизован, возвращаем JSON с информацией об этом
        return jsonify(authenticated=False)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        username = session['username']
        connection = sqlite3.connect('SearchWork.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM registration WHERE username=?', (username,))
        user = cursor.fetchone()

        cursor.execute('SELECT resume FROM registration WHERE username=?', (username,))
        resume_data = cursor.fetchone()

        cursor.execute('SELECT * FROM work WHERE workAdder=?', (username,))
        vacancies = cursor.fetchall()

        cursor.execute('SELECT * FROM otclick WHERE main=?', (username,))
        responses = cursor.fetchall()

        for i, response in enumerate(responses):
            cursor.execute('SELECT last_name FROM registration WHERE username=?', (response[0],))
            user_data = cursor.fetchone()
            if user_data:
                last_name = user_data[0]
                responses[i] = (*response[:-1], last_name)

        connection.close()

        if user:
            is_employer = bool(user[11])

            # Передаем переменные в шаблон
            return render_template('profile.html', user=user, is_employer=is_employer, resume_data=resume_data, vacancies=vacancies, responses=responses)
        else:
            return "Пользователь не найден"
    else:
        return redirect(url_for('login_page'))


@app.route('/delete_vacancy', methods=['POST'])
def delete_vacancy():
    if 'username' in session:
        username = session['username']
        vacancy_id = request.form['vacancy_id']

        conn = sqlite3.connect('SearchWork.db')
        c = conn.cursor()

        # Проверяем, что пользователь является владельцем вакансии
        c.execute("SELECT workAdder FROM work WHERE id=? AND workAdder=?", (vacancy_id, username))
        result = c.fetchone()

        if result:
            # Удаляем вакансию из базы данных
            c.execute("DELETE FROM work WHERE id=?", (vacancy_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('profile'))
        else:
            conn.close()
            return "Вы не являетесь владельцем этой вакансии"
    else:
        return redirect(url_for('login_page'))

@app.route('/delete_response', methods=['POST'])
def delete_response():
    if 'username' in session:
        username = session['username']
        response_id = request.form['response_id']

        conn = sqlite3.connect('SearchWork.db')
        c = conn.cursor()

        # Проверяем, что отклик принадлежит текущему пользователю
        c.execute("SELECT main FROM otclick WHERE id=? AND main=?", (response_id, username))
        result = c.fetchone()

        if result:
            # Удаляем отклик из базы данных
            c.execute("DELETE FROM otclick WHERE id=?", (response_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('profile'))
        else:
            conn.close()
            return "Этот отклик не принадлежит вам"
    else:
        return redirect(url_for('login_page'))


@app.route('/accept_response', methods=['POST'])
def accept_response():
    if 'username' in session:
        response_id = request.form['response_id']

        conn = sqlite3.connect('SearchWork.db')
        c = conn.cursor()

        # Обновляем отклик в базе данных, добавляя строку "Принят"
        c.execute("UPDATE otclick SET status='Принят' WHERE id=?", (response_id,))
        conn.commit()

        conn.close()

        # После обновления отклика возвращаемся на страницу профиля
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login_page'))




@app.route('/create_work', methods=['GET'])
def create_work():
    return render_template('createWork.html')

@app.route('/submit_work', methods=['POST'])
def submit_work():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        active = request.form['active']
        fullDesc = request.form['fullDesc']
        review = request.form['review']
        organization = request.form['organization']
        paySystem = request.form['paySystem']
        workPlaces = request.form['workPlaces']
        education = request.form['education']
        responsibilities = request.form['responsibilities']
        additionally = request.form['additionally']
        workTime = request.form['workTime']

        # Получаем имя пользователя (работодателя) из сессии
        workAdder = session['username'] if 'username' in session else None

        conn = connect_db()
        cursor = conn.cursor()

        # Используем параметры в запросе, чтобы вставить данные и автоматически установить numberView в 0 и статус 'pending'
        cursor.execute('''
            INSERT INTO work (name, description, active, fullDesc, review, organization, paySystem, workPlaces, education, responsibilities, additionally, workTime, numberView, workAdder, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, active, fullDesc, review, organization, paySystem, workPlaces, education, responsibilities, additionally, workTime, 0, workAdder, 'pending'))

        conn.commit()
        conn.close()

        return redirect(url_for('profile'))



@app.route("/entrance")
def show_Lk():
    # Проверяем, авторизован ли пользователь
    if 'username' in session:
        # Если пользователь авторизован, возвращаем его на страницу menu.html
        return redirect(url_for('menu'))
    else:
        # Если пользователь не авторизован, сохраняем параметры запроса для передачи после авторизации
        redirect_url = request.url
        session['redirect_url'] = redirect_url
        # Здесь происходит перенаправление на страницу входа (введите свой код для этого маршрута)
        # Например:
        return render_template('entrance.html')


@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    # Здесь нужно отобразить страницу входа (форму для ввода логина и пароля)
    # Пример:
    return render_template('entrance.html')

@app.route("/registration")
def show_reg():
    return render_template("registration.html")

@app.route("/searchWork")
def show_work():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work WHERE status = 'approved'")
    data = cursor.fetchall()
    conn.close()
    return render_template('work.html', data=data)

@app.route('/go')
def details():
    id = request.args.get('id')
    title = request.args.get('title')
    description = request.args.get('description')
    active = request.args.get('active')
    fullDesc = request.args.get('fullDesc')
    numberView = request.args.get('numberView')
    review = request.args.get('review')
    organization = request.args.get('organization')
    paySystem = request.args.get('paySystem')
    workPlaces = request.args.get('workPlaces')
    education = request.args.get('education')
    responsibilities = request.args.get('responsibilities')
    additionally = request.args.get('additionally')
    workTime = request.args.get('workTime')

    return render_template('workDesc.html', id=id, title=title, description=description, active=active, fullDesc=fullDesc, numberView=numberView, review=review, organization=organization, paySystem=paySystem, workPlaces=workPlaces, education=education, responsibilities=responsibilities, additionally=additionally, workTime=workTime)


@app.route('/submit_employer', methods=['POST'])
def submit_employer():
    if 'username' in session:
        username = session['username']

        name_organization = request.form['name_organization']
        activity = request.form['activity']
        address = request.form['address']
        phone_number = request.form['phone_number']
        FIO_boss = request.form['FIO_boss']

        conn = connect_db()
        c = conn.cursor()
        c.execute(
            "UPDATE registration SET name_organization=?, activity=?, address=?, phone_number=?, FIO_boss=? WHERE username=?",
            (name_organization, activity, address, phone_number, FIO_boss, username))
        conn.commit()
        conn.close()

        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login_page'))



@app.route('/check_employer_data', methods=['GET', 'POST'])
def check_employer_data():
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']

            # Проверяем, есть ли данные организации у пользователя
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute('SELECT name_organization FROM registration WHERE username=?', (username,))
            org_data = cursor.fetchone()
            connection.close()

            if org_data and org_data[0]:  # Если данные организации есть
                return redirect(url_for('search_worked'))  # Перенаправляем на страницу поиска сотрудников
            else:
                flash('Доступ к этой странице разрешен только для работодателей!')
                return redirect(url_for('menu'))  # Перенаправляем на главное меню
        elif request.method == 'GET':
            flash('Доступ к этой странице разрешен только для работодателей!')
            return redirect(url_for('menu'))  # Перенаправляем на главное меню
    else:
        return redirect(url_for('login_page'))




@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return 'Пользователь не авторизован'

    username = session['username']

    if 'file' not in request.files:
        return 'Файл не найден'

    file = request.files['file']
    if file.filename == '':
        return 'Файл не выбран'

    if file.mimetype != 'application/pdf':
        return 'Неверный формат файла. Пожалуйста, выберите PDF файл.'

    # Получаем путь к текущему резюме пользователя
    current_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], username + '.pdf')

    # Если у пользователя уже есть резюме, удаляем его
    if os.path.exists(current_resume_path):
        os.remove(current_resume_path)

    # Сохраняем новое резюме на сервере
    file.save(current_resume_path)

    return redirect(url_for('summary'))



from flask import send_file, make_response

@app.route('/download_file/<filename>')
def download_file(filename):
    # Путь к директории, где хранятся файлы для скачивания
    directory = 'download'
    return send_from_directory(directory, filename)

@app.route('/apply_form')
def apply_form():
    if 'username' in session:
        username = session['username']

        # Получаем переданные параметры о резюме из URL
        resume_id = request.args.get('id')
        title = request.args.get('title')
        description = request.args.get('description')
        active = request.args.get('active')
        fullDesc = request.args.get('fullDesc')
        review = request.args.get('review')
        organization = request.args.get('organization')
        paySystem = request.args.get('paySystem')
        workPlaces = request.args.get('workPlaces')
        education = request.args.get('education')
        responsibilities = request.args.get('responsibilities')
        additionally = request.args.get('additionally')
        workTime = request.args.get('workTime')

        conn = sqlite3.connect('SearchWork.db')
        c = conn.cursor()

        c.execute("SELECT resume FROM registration WHERE username=?", (username,))
        resume_data = c.fetchone()  # Получаем данные резюме пользователя из базы данных

        conn.close()

        return render_template('apply_form.html',
                               resume_id=resume_id, title=title, description=description,
                               active=active, fullDesc=fullDesc, review=review,
                               organization=organization, paySystem=paySystem,
                               workPlaces=workPlaces, education=education,
                               responsibilities=responsibilities, additionally=additionally,
                               workTime=workTime, resume_data=resume_data)  # Передаем resume_data в шаблон
    else:
        return redirect(url_for('login_page'))

@app.route('/submit_application', methods=['POST'])
def submit_application():
    if 'username' not in session:
        return 'Пользователь не авторизован'

    username = session['username']
    resume_id = request.form['resume_id']
    comment = request.form['comment']

    conn = sqlite3.connect('SearchWork.db')
    c = conn.cursor()

    # Получаем информацию о пользователе из таблицы registration по его username
    c.execute("SELECT id FROM registration WHERE username=?", (username,))
    user_id = c.fetchone()

    if user_id:
        user_id = user_id[0]
        # Получаем информацию о пользователе из таблицы registration по его id
        c.execute("SELECT last_name, phone FROM registration WHERE id=?", (user_id,))
        user_info = c.fetchone()
    else:
        conn.close()
        return 'Ошибка: пользователь не найден'

    # Получаем информацию о вакансии из таблицы work по идентификатору резюме
    c.execute("SELECT name, workAdder FROM work WHERE id=?", (resume_id,))
    work_info = c.fetchone()

    if work_info:
        job_name, work_adder = work_info
        if user_info:
            last_name, phone = user_info
            # Записываем отклик в таблицу otclick
            c.execute("INSERT INTO otclick (user, main, otziv, prof, fam, phone) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, work_adder, comment, job_name, last_name, phone))
            conn.commit()
            conn.close()
            return redirect(url_for('menu'))
        else:
            conn.close()
            return 'Ошибка: данные о пользователе не найдены'
    else:
        conn.close()
        return 'Ошибка: вакансия не найдена'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, use_reloader=False, debug=True)