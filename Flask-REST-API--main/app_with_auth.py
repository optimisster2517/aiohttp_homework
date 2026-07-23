from flask import Flask, request, jsonify
from datetime import datetime
from functools import wraps
import uuid
import hashlib
import secrets

app = Flask(__name__)

# Временное хранилище (в продакшене используйте БД)
advertisements = {}
users = {}
sessions = {}  # token: user_id


def hash_password(password):
    """Хеширование пароля с солью"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(stored_password, provided_password):
    """Проверка пароля"""
    salt, pwd_hash = stored_password.split('$')
    return pwd_hash == hashlib.sha256((provided_password + salt).encode()).hexdigest()


def require_auth(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Убираем префикс "Bearer " если есть
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id = sessions.get(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Добавляем user_id в kwargs
        kwargs['current_user_id'] = user_id
        return f(*args, **kwargs)
    
    return decorated_function


# ============== ROUTES ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==============

@app.route('/api/users/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email']
    
    # Проверка, что пользователь не существует
    if any(user['email'] == email for user in users.values()):
        return jsonify({'error': 'User already exists'}), 409
    
    # Создание пользователя
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'email': email,
        'password_hash': hash_password(data['password']),
        'created_at': datetime.now().isoformat()
    }
    
    users[user_id] = user
    
    return jsonify({
        'id': user_id,
        'email': email,
        'created_at': user['created_at']
    }), 201


@app.route('/api/users/login', methods=['POST'])
def login():
    """Авторизация пользователя"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Поиск пользователя по email
    user = None
    for u in users.values():
        if u['email'] == data['email']:
            user = u
            break
    
    if not user or not verify_password(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Создание токена сессии
    token = secrets.token_urlsafe(32)
    sessions[token] = user['id']
    
    return jsonify({
        'token': token,
        'user_id': user['id'],
        'email': user['email']
    }), 200


@app.route('/api/users/logout', methods=['POST'])
@require_auth
def logout(current_user_id):
    """Выход из системы"""
    token = request.headers.get('Authorization')
    if token.startswith('Bearer '):
        token = token[7:]
    
    if token in sessions:
        del sessions[token]
    
    return jsonify({'message': 'Logged out successfully'}), 200


# ============== ROUTES ДЛЯ ОБЪЯВЛЕНИЙ ==============

@app.route('/api/advertisements', methods=['POST'])
@require_auth
def create_advertisement(current_user_id):
    """Создание нового объявления (только для авторизованных)"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'title' not in data or 'description' not in data:
        return jsonify({'error': 'Missing required fields: title, description'}), 400
    
    # Создание объявления
    ad_id = str(uuid.uuid4())
    advertisement = {
        'id': ad_id,
        'title': data['title'],
        'description': data['description'],
        'created_at': datetime.now().isoformat(),
        'owner': current_user_id
    }
    
    advertisements[ad_id] = advertisement
    
    return jsonify(advertisement), 201


@app.route('/api/advertisements/<ad_id>', methods=['GET'])
def get_advertisement(ad_id):
    """Получение объявления по ID"""
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    return jsonify(advertisement), 200


@app.route('/api/advertisements', methods=['GET'])
def get_all_advertisements():
    """Получение всех объявлений"""
    return jsonify(list(advertisements.values())), 200


@app.route('/api/advertisements/<ad_id>', methods=['PUT', 'PATCH'])
@require_auth
def update_advertisement(ad_id, current_user_id):
    """Редактирование объявления (только владелец)"""
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    # Проверка прав доступа
    if advertisement['owner'] != current_user_id:
        return jsonify({'error': 'You can only edit your own advertisements'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Обновление полей
    if 'title' in data:
        advertisement['title'] = data['title']
    if 'description' in data:
        advertisement['description'] = data['description']
    
    advertisement['updated_at'] = datetime.now().isoformat()
    advertisements[ad_id] = advertisement
    
    return jsonify(advertisement), 200


@app.route('/api/advertisements/<ad_id>', methods=['DELETE'])
@require_auth
def delete_advertisement(ad_id, current_user_id):
    """Удаление объявления (только владелец)"""
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    # Проверка прав доступа
    if advertisement['owner'] != current_user_id:
        return jsonify({'error': 'You can only delete your own advertisements'}), 403
    
    del advertisements[ad_id]
    
    return jsonify({'message': 'Advertisement deleted successfully'}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'ok',
        'advertisements_count': len(advertisements),
        'users_count': len(users),
        'active_sessions': len(sessions)
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
