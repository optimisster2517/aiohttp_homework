"""aiohttp API объявлений с авторизацией.

Хранение данных (пользователи и объявления) реализовано полностью асинхронно
через async SQLAlchemy (async engine + AsyncSession). Пароли хэшируются bcrypt,
токены выдаются в формате JWT (Bearer).
"""
import os
import json
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from aiohttp import web
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import Session, User, Advertisement, init_db, close_db

# Секрет и параметры JWT (в продакшене брать из секрет-хранилища).
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

app = web.Application()


def hash_password(password: str) -> str:
    """Хеширование пароля с помощью bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Проверка пароля против bcrypt-хэша."""
    try:
        return bcrypt.checkpw(provided_password.encode(), stored_hash.encode())
    except ValueError:
        return False


def create_token(user_id: str) -> str:
    """Создание JWT-токена для пользователя."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=JWT_EXPIRES_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    """Декодирование JWT-токена, возвращает user_id или None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_token_from_request(request):
    """Извлечение Bearer-токена из заголовка Authorization."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return auth_header


def require_auth(handler):
    """Декоратор для проверки авторизации по JWT."""
    async def wrapped(request):
        token = get_token_from_request(request)

        if not token:
            return web.json_response({'error': 'Authorization required'}, status=401)

        user_id = decode_token(token)
        if not user_id:
            return web.json_response({'error': 'Invalid or expired token'}, status=401)

        request['current_user_id'] = user_id
        return await handler(request)

    return wrapped


def require_ownership(handler):
    """Декоратор для проверки прав владельца объявления (асинхронно)."""
    async def wrapped(request):
        ad_id = request.match_info['ad_id']

        async with Session() as session:
            advertisement = await session.get(Advertisement, ad_id)

            if not advertisement:
                return web.json_response({'error': 'Advertisement not found'}, status=404)

            if advertisement.owner_id != request['current_user_id']:
                return web.json_response(
                    {'error': 'You can only edit/delete your own advertisements'},
                    status=403
                )

        return await handler(request)

    return wrapped


# ============== ROUTES ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==============

async def register(request):
    """Регистрация нового пользователя."""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

    if not data or 'email' not in data or 'password' not in data:
        return web.json_response({'error': 'Email and password required'}, status=400)

    async with Session() as session:
        user = User(email=data['email'], password_hash=hash_password(data['password']))
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return web.json_response({'error': 'User already exists'}, status=409)

        return web.json_response(user.to_dict(), status=201)


async def login(request):
    """Авторизация пользователя, выдача JWT-токена."""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

    if not data or 'email' not in data or 'password' not in data:
        return web.json_response({'error': 'Email and password required'}, status=400)

    async with Session() as session:
        result = await session.execute(select(User).where(User.email == data['email']))
        user = result.scalar_one_or_none()

        if not user or not verify_password(user.password_hash, data['password']):
            return web.json_response({'error': 'Invalid email or password'}, status=401)

        token = create_token(user.id)
        return web.json_response({
            'token': token,
            'user_id': user.id,
            'email': user.email
        }, status=200)


@require_auth
async def logout(request):
    """Выход из системы.

    С JWT токены не хранятся на сервере (stateless), поэтому клиенту достаточно
    удалить токен у себя. Эндпоинт оставлен для совместимости API.
    """
    return web.json_response({'message': 'Logged out successfully'}, status=200)


# ============== ROUTES ДЛЯ ОБЪЯВЛЕНИЙ ==============

@require_auth
async def create_advertisement(request):
    """Создание нового объявления (только для авторизованных)."""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

    if not data:
        return web.json_response({'error': 'No data provided'}, status=400)

    if 'title' not in data or 'description' not in data:
        return web.json_response(
            {'error': 'Missing required fields: title, description'},
            status=400
        )

    async with Session() as session:
        advertisement = Advertisement(
            title=data['title'],
            description=data['description'],
            owner_id=request['current_user_id'],
        )
        session.add(advertisement)
        await session.commit()
        await session.refresh(advertisement)
        return web.json_response(advertisement.to_dict(), status=201)


async def get_advertisement(request):
    """Получение объявления по ID."""
    ad_id = request.match_info['ad_id']

    async with Session() as session:
        advertisement = await session.get(Advertisement, ad_id)
        if not advertisement:
            return web.json_response({'error': 'Advertisement not found'}, status=404)
        return web.json_response(advertisement.to_dict(), status=200)


async def get_all_advertisements(request):
    """Получение всех объявлений."""
    async with Session() as session:
        result = await session.execute(select(Advertisement))
        ads = result.scalars().all()
        return web.json_response([ad.to_dict() for ad in ads], status=200)


@require_auth
@require_ownership
async def update_advertisement(request):
    """Редактирование объявления (только владелец)."""
    ad_id = request.match_info['ad_id']

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

    if not data:
        return web.json_response({'error': 'No data provided'}, status=400)

    async with Session() as session:
        advertisement = await session.get(Advertisement, ad_id)
        if not advertisement:
            return web.json_response({'error': 'Advertisement not found'}, status=404)

        if 'title' in data:
            advertisement.title = data['title']
        if 'description' in data:
            advertisement.description = data['description']

        await session.commit()
        await session.refresh(advertisement)
        return web.json_response(advertisement.to_dict(), status=200)


@require_auth
@require_ownership
async def delete_advertisement(request):
    """Удаление объявления (только владелец)."""
    ad_id = request.match_info['ad_id']

    async with Session() as session:
        advertisement = await session.get(Advertisement, ad_id)
        if not advertisement:
            return web.json_response({'error': 'Advertisement not found'}, status=404)
        await session.delete(advertisement)
        await session.commit()

    return web.json_response({'message': 'Advertisement deleted successfully'}, status=200)


async def health_check(request):
    """Проверка работоспособности API."""
    from sqlalchemy import func

    async with Session() as session:
        ads_count = await session.scalar(select(func.count()).select_from(Advertisement))
        users_count = await session.scalar(select(func.count()).select_from(User))

    return web.json_response({
        'status': 'ok',
        'advertisements_count': ads_count,
        'users_count': users_count,
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


async def on_startup(app):
    await init_db()


async def on_cleanup(app):
    await close_db()


if __name__ == '__main__':
    setup_routes()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host='0.0.0.0', port=8080)
