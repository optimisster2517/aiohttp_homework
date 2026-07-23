from aiohttp import web, WSMsgType
from datetime import datetime
import uuid
import json

app = web.Application()

# Временное хранилище объявлений (в реальном проекте используйте БД)
advertisements = {}


async def create_advertisement(request):
    """Создание нового объявления"""
    try:
        data = await request.json()
        
        # Валидация данных
        if not data:
            return web.json_response({'error': 'No data provided'}, status=400)
        
        if 'title' not in data or 'description' not in data or 'owner' not in data:
            return web.json_response(
                {'error': 'Missing required fields: title, description, owner'}, 
                status=400
            )
        
        # Создание объявления
        ad_id = str(uuid.uuid4())
        advertisement = {
            'id': ad_id,
            'title': data['title'],
            'description': data['description'],
            'created_at': datetime.now().isoformat(),
            'owner': data['owner']
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


async def update_advertisement(request):
    """Редактирование объявления"""
    ad_id = request.match_info['ad_id']
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return web.json_response({'error': 'Advertisement not found'}, status=404)
    
    try:
        data = await request.json()
        
        if not data:
            return web.json_response({'error': 'No data provided'}, status=400)
        
        # Обновление полей
        if 'title' in data:
            advertisement['title'] = data['title']
        if 'description' in data:
            advertisement['description'] = data['description']
        
        advertisements[ad_id] = advertisement
        
        return web.json_response(advertisement, status=200)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON'}, status=400)


async def delete_advertisement(request):
    """Удаление объявления"""
    ad_id = request.match_info['ad_id']
    
    if ad_id not in advertisements:
        return web.json_response({'error': 'Advertisement not found'}, status=404)
    
    del advertisements[ad_id]
    
    return web.json_response({'message': 'Advertisement deleted successfully'}, status=200)


async def health_check(request):
    """Проверка работоспособности API"""
    return web.json_response({
        'status': 'ok', 
        'advertisements_count': len(advertisements)
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


if __name__ == '__main__':
    setup_routes()
    web.run_app(app, host='0.0.0.0', port=8080)
