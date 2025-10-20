from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import string
import json

# --- КОНФИГУРАЦИЯ ---
app = Flask(__name__)
# Установите безопасный секретный ключ!
app.secret_key = os.environ.get('SECRET_KEY') or 'strong_default_secret_key_12345'
DATA_FILE = 'users.json'

# --- ФУНКЦИИ УПРАВЛЕНИЯ ДАННЫМИ (I/O) ---

def load_users():
    """Загружает данные пользователей из JSON-файла."""
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_users(users):
    """Сохраняет данные пользователей в JSON-файл."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def update_user_history(username, new_password_raw):
    """
    ⚠️ ИСПРАВЛЕНО: Только добавляет сырой пароль в историю. 
    Текущий пароль для входа (password_hash) НЕ меняется.
    """
    users = load_users()
    if username in users:
        # Добавляем сырой пароль в историю
        users[username]['history'].append(new_password_raw)
        save_users(users)

# --- ФУНКЦИЯ ГЕНЕРАЦИИ ПАРОЛЕЙ ---

def generate_password(length, use_lowercase, use_uppercase, use_digits, use_symbols):
    """Генерирует случайный пароль по заданным параметрам."""
    characters = ''
    if use_lowercase:
        characters += string.ascii_lowercase
    if use_uppercase:
        characters += string.ascii_uppercase
    if use_digits:
        characters += string.digits
    if use_symbols:
        characters += string.punctuation

    if not characters:
        return "Ошибка: выберите хотя бы один тип символов."

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

# --- ДЕКОРАТОР АВТОРИЗАЦИИ ---

def login_required(f):
    """Декоратор для защиты маршрутов, требующих авторизации."""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# --- ОБРАБОТЧИКИ МАРШРУТОВ (VIEWS) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Обработка регистрации нового пользователя."""
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        
        if not username or not password:
            message = 'Логин и пароль не могут быть пустыми.'
        elif username in users:
            message = 'Такой логин уже существует.'
        else:
            # Хеширование пароля для входа
            hashed_password = generate_password_hash(password)
            
            users[username] = {
                'password_hash': hashed_password,
                'history': [] # История начинается пустой
            }
            save_users(users)
            flash('Пользователь зарегистрирован. Можете войти.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Обработка входа пользователя."""
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        
        # Проверка хеша пароля
        if username in users and check_password_hash(users[username]['password_hash'], password):
            session['username'] = username
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            message = 'Неверный логин или пароль.'
            
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    """Выход из системы."""
    session.pop('username', None)
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Главная страница: Генератор паролей и отображение истории."""
    length = 12
    use_lowercase = True
    use_uppercase = True
    use_digits = True
    use_symbols = False
    
    password = None 
    username = session['username']
    users = load_users()
    
    user_history = users.get(username, {}).get('history', [])

    if request.method == 'POST':
        try:
            length = int(request.form.get('length', 12))
            
            if length < 1:
                password = "Ошибка: длина должна быть больше 0."
            else:
                use_lowercase = 'lowercase' in request.form
                use_uppercase = 'uppercase' in request.form
                use_digits = 'digits' in request.form
                use_symbols = 'symbols' in request.form

                raw_password = generate_password(length, use_lowercase, use_uppercase, use_digits, use_symbols)
                
                if raw_password.startswith("Ошибка:"):
                    password = raw_password
                else:
                    # ⚠️ ИСПРАВЛЕНО: Вызываем функцию ТОЛЬКО для обновления истории
                    update_user_history(username, raw_password)
                    
                    password = raw_password
                    
                    # Обновляем историю для отображения
                    user_history = load_users().get(username, {}).get('history', [])
                    flash('Пароль успешно сгенерирован и добавлен в историю!', 'success')
                    
        except (ValueError, TypeError):
            password = "Ошибка: введите корректную длину."

    return render_template('index.html',
                           password=password,
                           length=length,
                           use_lowercase=use_lowercase,
                           use_uppercase=use_uppercase,
                           use_digits=use_digits,
                           use_symbols=use_symbols,
                           user_history=user_history)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5500, debug=True)