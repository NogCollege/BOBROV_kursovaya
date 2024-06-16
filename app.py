from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from filters import split_into_lines
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'stepan_olegovich'

app.jinja_env.filters['split_into_lines'] = split_into_lines


# Настройки для загрузки файлов
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Функция для создания таблицы
def create_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, bio TEXT, age INTEGER, city TEXT photo TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Главная страница
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('main'))
    return render_template('index.html')

# Регистрация
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return 'Пользователь с таким логином уже существует. Пожалуйста, выберите другой логин.'
    
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()
    
    return redirect(url_for('login'))

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return 'Неверный логин или пароль. Попробуйте еще раз.'
    return render_template('index.html')

@app.route('/main')
def main():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('main.html', user=user)

# Редактирование профиля
@app.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_bio = request.form['bio']
        username = session['username']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Обновляем биографию пользователя
        cursor.execute('UPDATE users SET bio = ? WHERE username = ?', (new_bio, username))
        conn.commit()

        conn.close()

        return redirect(url_for('profile'))

    # Если метод GET, отображаем форму для редактирования
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT bio FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('edit_profile.html', bio=user['bio'])
# Профиль пользователя (собственный)
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('profile.html', user=user)

# Профиль пользователя (другого пользователя)
@app.route('/profile/<username>')
def view_profile(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('view_profile.html', user=user)
    else:
        return 'Пользователь не найден', 404

# Добавление в друзья
@app.route('/add_friend/<username>', methods=['POST'])
def add_friend(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем id пользователя, которого добавляем в друзья
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    friend = cursor.fetchone()

    if friend:
        friend_id = friend['id']
        # Добавляем запись в таблицу друзей
        cursor.execute('INSERT INTO friends (user_id, friend_id) VALUES (?, ?)', (user_id, friend_id))
        conn.commit()

    conn.close()
    return redirect(url_for('view_profile', username=username))

# Принятие заявки в друзья
@app.route('/accept_friend/<username>', methods=['POST'])
def accept_friend(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем id пользователя, который отправил заявку в друзья
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    friend = cursor.fetchone()

    if friend:
        friend_id = friend['id']
        # Добавляем запись в таблицу друзей
        cursor.execute('INSERT INTO friends (user_id, friend_id) VALUES (?, ?)', (user_id, friend_id))
        conn.commit()

    conn.close()
    return redirect(url_for('view_profile', username=username))

# Удаление из друзей
@app.route('/remove_friend/<username>', methods=['POST'])
def remove_friend(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем id пользователя, которого удаляем из друзей
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    friend = cursor.fetchone()

    if friend:
        friend_id = friend['id']
        # Удаляем запись из таблицы друзей
        cursor.execute('DELETE FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)',
                       (user_id, friend_id, friend_id, user_id))
        conn.commit()

    conn.close()
    return redirect(url_for('view_profile', username=username))

# Страница с друзьями
@app.route('/friend')
def friend():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем список друзей пользователя
    cursor.execute('''
        SELECT u.username
        FROM users u
        JOIN friends f ON u.id = f.friend_id
        WHERE f.user_id = ?
    ''', (user_id,))
    friends = cursor.fetchall()
    conn.close()

    return render_template('friend.html', friends=friends)

# Чат
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    
    if request.method == 'POST':
        username = session['username']
        message = request.form['message'][:300]  # Ограничиваем длину сообщения до 300 символов
        
        cursor.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
        conn.commit()
        
        # Закрываем соединение после выполнения запроса
        conn.close()
        
        return redirect(url_for('chat'))  # Перенаправляем обратно на страницу чата после отправки сообщения

    conn.close()

    return render_template('chat.html', messages=messages)



@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    message = request.form['message']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
    conn.commit()
    conn.close()

    return redirect(url_for('chat'))

@app.route('/users')
def users():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()

    return render_template('users_list.html', users=users)

def create_private_messages_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS private_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_username TEXT,
                        receiver_username TEXT,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()



@app.route('/chat/<username>', methods=['GET', 'POST'])
def private_chat(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = session['username']

    if request.method == 'POST':
        message = request.form['message']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO private_messages (sender_username, receiver_username, message) VALUES (?, ?, ?)',
                       (current_user, username, message))
        conn.commit()
        conn.close()

        return redirect(url_for('private_chat', username=username))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM private_messages 
                      WHERE (sender_username = ? AND receiver_username = ?) 
                         OR (sender_username = ? AND receiver_username = ?)
                      ORDER BY timestamp ASC''', (current_user, username, username, current_user))
    messages = cursor.fetchall()
    conn.close()

    return render_template('private_chat.html', messages=messages, receiver=username)












# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    create_table()
    create_private_messages_table()
    app.run(debug=True)