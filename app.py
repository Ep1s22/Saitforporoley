from flask import Flask, render_template, request, redirect, session
import random
import string
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your_secret_key_change_in_production'

users = {
    'admin': 'password123',
    'user1': 'abc123',
    'test': 'testpass'
}

def generate_password(length, use_lowercase, use_uppercase, use_digits, use_symbols):
    """Генерирует пароль на основе выбранных критериев."""
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
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
def index():
    # Проверка авторизации
    if 'username' not in session:
        return redirect('/login')

    # Значения по умолчанию
    length = 12
    use_lowercase = True
    use_uppercase = True
    use_digits = True
    use_symbols = False
    password = None

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
        except (ValueError, TypeError):
            password = "Ошибка: введите корректную длину."

    return render_template('index.html',
                           password=password,
                           length=length,
                           use_lowercase=use_lowercase,
                           use_uppercase=use_uppercase,
                           use_digits=use_digits,
                           use_symbols=use_symbols)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)