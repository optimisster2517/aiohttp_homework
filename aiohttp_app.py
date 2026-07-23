"""aiohttp API объявлений (базовая версия без авторизации).

Хранение объявлений реализовано асинхронно через async SQLAlchemy.
Базовая версия использует отдельного «системного» пользователя как владельца,
так как объявления в БД привязаны к пользователю (owner_id).
"""
import json

from aiohttp import web
from sqlalchemy import select, func

from models import Session, User, Advertisement, init_db, close_db

app = web.Application()

# Идентификатор служебного владельца для базовой версии без авторизации.
DEFAULT_OWNER_EMAIL = "system@local"


async def _get_owner_id(session, requested_owner: str | None = None) -> str:
    """Получить (или создать) пользователя-владельца по email."""
    email = requested_owner or DEFAULT_OWNER_EMAIL
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, password_hash="-")
        session.add(user)
        await session.flush()
    return user.id


async def create_advertisement(request):
    """Создание нового объявления."""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)

    if not data:
        return web.json_response({'error': 'No data provided'}, status=400)

    if 'title' not in data or 'description' not in data or 'owner' not in data:
        return web.json_response(
            {'error': 'Missing required fields: title, description, owner'},
            status=400
        )

    async with Session() as session:
        owner_id = await _get_owner_id(session, str(data['owner']))
        advertisement = Advertisement(
            title=data['title'],
            description=data['description'],
            owner_id=owner_id,
        )
        session.add(advertisement)
        await session.commit()
        await session.refresh(advertisement)
        result = advertisement.to_dict()
        result['owner'] = str(data['owner'])
        return web.json_response(result, status=201)


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


async def update_advertisement(request):
    """Редактирование объявления."""
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


async def delete_advertisement(request):
    """Удаление объявления."""
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
    async with Session() as session:
        ads_count = await session.scalar(select(func.count()).select_from(Advertisement))
    return web.json_response({
        'status': 'ok',
        'advertisements_count': ads_count
    }, status=200)


# Настройка маршрутов
def setup_routes():
    app.router.add_post('/api/advertisements', create_advertisement)
    app.router.add_get('/api/advertisements/{ad_id}', get_advertisement)
    app.router.add_get('/api/advertisements', get_all_advertisements)
    app.router.add_put('/api/advertisements/{ad_id}', update_advertisement)
    app.router.add_patch('/api/advertisements/{ad_id}', update_advertisement)
    app.router.add_delete('/api/advertisements/{ad_id}', delete_advertisement)
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
