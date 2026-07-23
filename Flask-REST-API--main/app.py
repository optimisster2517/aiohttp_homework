from flask import Flask, request, jsonify
from datetime import datetime
import uuid

app = Flask(__name__)

# Временное хранилище объявлений (в реальном проекте используйте БД)
advertisements = {}


@app.route('/api/advertisements', methods=['POST'])
def create_advertisement():
    """Создание нового объявления"""
    data = request.get_json()
    
    # Валидация данных
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'title' not in data or 'description' not in data or 'owner' not in data:
        return jsonify({'error': 'Missing required fields: title, description, owner'}), 400
    
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
def update_advertisement(ad_id):
    """Редактирование объявления"""
    advertisement = advertisements.get(ad_id)
    
    if not advertisement:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Обновление полей
    if 'title' in data:
        advertisement['title'] = data['title']
    if 'description' in data:
        advertisement['description'] = data['description']
    
    advertisements[ad_id] = advertisement
    
    return jsonify(advertisement), 200


@app.route('/api/advertisements/<ad_id>', methods=['DELETE'])
def delete_advertisement(ad_id):
    """Удаление объявления"""
    if ad_id not in advertisements:
        return jsonify({'error': 'Advertisement not found'}), 404
    
    del advertisements[ad_id]
    
    return jsonify({'message': 'Advertisement deleted successfully'}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({'status': 'ok', 'advertisements_count': len(advertisements)}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
