from aiohttp import web
from datetime import datetime
import uuid
import hashlib
import secrets
import json

app = web.Application()

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


def get_token_from_request(request):
    """Извлечение токена из заголовка Authorization"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Убираем префикс "Bearer " если есть
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    return auth_header


def require_auth(handler):
    """Декоратор для проверки авторизации"""
    async def wrapped(request):
        token = get_token_from_request(request)
        
        if not token:
            return web.json_response({'error': 'Authorization required'}, status=401)
        
        user_id = sessions.get(token)
        if not user_id:
            return web.json_response({'error': 'Invalid or expired token'}, status=401)
        
        # Добавляем user_id в request
        request['current_user_id'] = user_id
        return await handler(request)
    
    return wrapped


def require_ownership(handler):
    """Декоратор для проверки прав владельца объявления"""
    async def wrapped(request):
        ad_id = request.match_info['ad_id']
        advertisement = advertisements.get(ad_id)
        
        if not advertisement:
            return web.json_response({'error': 'Advertisement not found'}, status=404)
        
        current_user_id = request['current_user_id']
        if advertisement['owner'] != current_user_id:
            return web.json_response(
                {'error': 'You can only edit/delete your own advertisements'}, 
                status=403
            )
        
        return await handler(request)
    
    return wrapped


# ============== ROUTES ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==============

async def register(request):
    """Регистрация нового пользователя"""
    try:
        data = await request.json()
        
        if not data or 'email' not in data or 'password' not in data:
            return web.json_response({'error': 'Email and password required'}, status=400)
        
        email = data['email']
        
        # Проверка, что пользователь не существует
        if any(user['email'] == email for user in users.values()):
            return web.json_response({'error': 'User already exists'}, status=409)
        
        # Создание пользователя
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'email': email,
            'password_hash': hash_password(data['password']),
            'created_at': datetime.now().isoformat()
        }
        
        users[user_id] = user
        
        return web.json_response({
            'id': user_id,
            'email': email,
            'created_at': user['created_at']
        }, status=201)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)


async def login(request):
    """Авторизация пользователя"""
    try:
        data = await request.json()
        
        if not data or 'email' not in data or 'password' not in data:
            return web.json_response({'error': 'Email and password required'}, status=400)
        
        # Поиск пользователя по email
        user = None
        for u in users.values():
            if u['email'] == data['email']:
                user = u
                break
        
        if not user or not verify_password(user['password_hash'], data['password']):
            return web.json_response({'error': 'Invalid email or password'}, status=401)
        
        # Создание токена сессии
        token = secrets.token_urlsafe(32)
        sessions[token] = user['id']
        
        return web.json_response({
            'token': token,
            'user_id': user['id'],
            'email': user['email']
        }, status=200)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)


@require_auth
async def logout(request):
    """Выход из системы"""
    token = get_token_from_request(request)
    
    if token and token in sessions:
        del sessions[token]
    
    return web.json_response({'message': 'Logged out successfully'}, status=200)


# ============== ROUTES ДЛЯ ОБЪЯВЛЕНИЙ ==============

@require_auth
async def create_advertisement(request):
    """Создание нового объявления (только для авторизованных)"""
    try:
        data = await request.json()
        
        if not data:
            return web.json_response({'error': 'No data provided'}, status=400)
        
        if 'title' not in data or 'description' not in data:
            return web.json_response(
                {'error': 'Missing required fields: title, description'}, 
                status=400
            )
        
        # Создание объявления
        ad_id = str(uuid.uuid4())
        advertisement = {
            'id': ad_id,
            'title': data['title'],
            'description': data['description'],
            'created_at': datetime.now().isoformat(),
            'owner': request['current_user_id']
        }
        
        advertisements[ad_id] = advertisement
        
        return web.json_response(advertisement, status=201)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)


async def get_advertisement(request):
    """Получение объявления по ID"""
    ad_id = request.match_info['ad_id']
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return web.json_response({'error': 'Advertisement not found'}, status=404)
    
    return web.json_response(advertisement, status=200)


async def get_all_advertisements(request):
    """Получение всех объявлений"""
    return web.json_response(list(advertisements.values()), status=200)


@require_auth
@require_ownership
async def update_advertisement(request):
    """Редактирование объявления (только владелец)"""
    try:
        ad_id = request.match_info['ad_id']
        advertisement = advertisements[ad_id]
        
        data = await request.json()
        
        if not data:
            return web.json_response({'error': 'No data provided'}, status=400)
        
        # Обновление полей
        if 'title' in data:
            advertisement['title'] = data['title']
        if 'description' in data:
            advertisement['description'] = data['description']
        
        advertisement['updated_at'] = datetime.now().isoformat()
        advertisements[ad_id] = advertisement
        
        return web.json_response(advertisement, status=200)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)


@require_auth
@require_ownership
async def delete_advertisement(request):
    """Удаление объявления (только владелец)"""
    ad_id = request.match_info['ad_id']
    
    del advertisements[ad_id]
    
    return web.json_response({'message': 'Advertisement deleted successfully'}, status=200)


async def health_check(request):
    """Проверка работоспособности API"""
    return web.json_response({
        'status': 'ok',
        'advertisements_count': len(advertisements),
        'users_count': len(users),
        'active_sessions': len(sessions)
    }, status=200)


# Настройка маршрутов
def setup_routes():
    # Роуты для пользователей
    app.router.add_post('/api/users/register', register)
    app.router.add_post('/api/users/login', login)
    app.router.add_post('/api/users/logout', logout)
    
    # Роуты для объявлений
    app.router.add_post('/api/advertisements', create_advertisement)
    app.router.add_get('/api/advertisements/{ad_id}', get_advertisement)
    app.router.add_get('/api/advertisements', get_all_advertisements)
    app.router.add_put('/api/advertisements/{ad_id}', update_advertisement)
    app.router.add_patch('/api/advertisements/{ad_id}', update_advertisement)
    app.router.add_delete('/api/advertisements/{ad_id}', delete_advertisement)
    
    # Health check
    app.router.add_get('/api/health', health_check)


if __name__ == '__main__':
    setup_routes()
    web.run_app(app, host='0.0.0.0', port=8080)
