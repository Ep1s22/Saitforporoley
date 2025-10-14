from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your_secret_key_change_in_production'

DATA_FILE = 'users.txt'

def load_users():
    users = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        username = parts[0]
                        password = parts[1]
                        history = parts[2].split(',') if parts[2] else []
                        users[username] = {
                            'password': password,
                            'history': history
                        }
    return users

def save_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        for username, data in users.items():
            line = f"{username}|{data['password']}|{','.join(data['history'])}\n"
            f.write(line)

def update_user_password(username, new_password):
    users = load_users()
    if username in users:
        users[username]['password'] = new_password
        users[username]['history'].append(new_password)
        save_users(users)

def generate_password(length, use_lowercase, use_uppercase, use_digits, use_symbols):
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

# Декоратор для проверки авторизации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users:
            message = 'Такой логин уже существует.'
        else:
            users[username] = {
                'password': password,
                'history': [password]
            }
            save_users(users)
            message = 'Пользователь зарегистрирован. Можете войти.'
            return redirect(url_for('login'))
    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
@login_required
def login():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect('/')
        else:
            message = 'Неверный логин или пароль.'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    length = 12
    use_lowercase = True
    use_uppercase = True
    use_digits = True
    use_symbols = False
    password = None
    username = session['username']
    users = load_users()

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

                password = generate_password(length, use_lowercase, use_uppercase, use_digits, use_symbols)
                # Обновляем пароль и историю
                update_user_password(username, password)
        except (ValueError, TypeError):
            password = "Ошибка: введите корректную длину."

    return render_template('index.html',
                           password=password,
                           length=length,
                           use_lowercase=use_lowercase,
                           use_uppercase=use_uppercase,
                           use_digits=use_digits,
                           use_symbols=use_symbols,
                           users=load_users())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5500, debug=True)
