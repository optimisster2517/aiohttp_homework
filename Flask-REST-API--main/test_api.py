"""
Скрипт для тестирования REST API объявлений
Использование: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"


def print_response(response, title="Response"):
    """Красивый вывод ответа"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")


def test_basic_api():
    """Тестирование базового API (app.py)"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ БАЗОВОГО API (без авторизации)")
    print("=" * 60)
    
    # 1. Создание объявления
    print("\n1. Создание объявления...")
    ad_data = {
        "title": "Продам ноутбук",
        "description": "MacBook Pro 2020, 16GB RAM, 512GB SSD",
        "owner": "Ivan"
    }
    response = requests.post(f"{BASE_URL}/api/advertisements", json=ad_data)
    print_response(response, "Создание объявления")
    
    if response.status_code == 201:
        ad_id = response.json()["id"]
        print(f"✅ Объявление создано с ID: {ad_id}")
        
        # 2. Получение объявления
        print("\n2. Получение объявления по ID...")
        response = requests.get(f"{BASE_URL}/api/advertisements/{ad_id}")
        print_response(response, "Получение объявления")
        
        # 3. Получение всех объявлений
        print("\n3. Получение всех объявлений...")
        response = requests.get(f"{BASE_URL}/api/advertisements")
        print_response(response, "Все объявления")
        
        # 4. Обновление объявления
        print("\n4. Обновление объявления...")
        update_data = {
            "title": "Продам ноутбук (СРОЧНО)",
            "description": "Цена снижена! MacBook Pro 2020"
        }
        response = requests.put(f"{BASE_URL}/api/advertisements/{ad_id}", json=update_data)
        print_response(response, "Обновление объявления")
        
        # 5. Удаление объявления
        print("\n5. Удаление объявления...")
        response = requests.delete(f"{BASE_URL}/api/advertisements/{ad_id}")
        print_response(response, "Удаление объявления")
        
        # 6. Попытка получить удаленное объявление
        print("\n6. Попытка получить удаленное объявление...")
        response = requests.get(f"{BASE_URL}/api/advertisements/{ad_id}")
        print_response(response, "Получение удаленного объявления")


def test_auth_api():
    """Тестирование API с авторизацией (app_with_auth.py)"""
    print("\n\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ API С АВТОРИЗАЦИЕЙ")
    print("=" * 60)
    
    # 1. Регистрация первого пользователя
    print("\n1. Регистрация пользователя...")
    user1_data = {
        "email": "alice@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/users/register", json=user1_data)
    print_response(response, "Регистрация пользователя Alice")
    
    # 2. Регистрация второго пользователя
    print("\n2. Регистрация второго пользователя...")
    user2_data = {
        "email": "bob@example.com",
        "password": "password456"
    }
    response = requests.post(f"{BASE_URL}/api/users/register", json=user2_data)
    print_response(response, "Регистрация пользователя Bob")
    
    # 3. Авторизация первого пользователя
    print("\n3. Авторизация Alice...")
    response = requests.post(f"{BASE_URL}/api/users/login", json=user1_data)
    print_response(response, "Авторизация Alice")
    
    if response.status_code == 200:
        alice_token = response.json()["token"]
        print(f"✅ Токен Alice получен: {alice_token[:20]}...")
        
        # 4. Попытка создать объявление без токена
        print("\n4. Попытка создать объявление без авторизации...")
        ad_data = {
            "title": "Продам телефон",
            "description": "iPhone 15 Pro"
        }
        response = requests.post(f"{BASE_URL}/api/advertisements", json=ad_data)
        print_response(response, "Создание без токена")
        
        # 5. Создание объявления с токеном Alice
        print("\n5. Создание объявления с токеном Alice...")
        headers = {"Authorization": f"Bearer {alice_token}"}
        response = requests.post(f"{BASE_URL}/api/advertisements", json=ad_data, headers=headers)
        print_response(response, "Создание с токеном Alice")
        
        if response.status_code == 201:
            ad_id = response.json()["id"]
            print(f"✅ Объявление создано с ID: {ad_id}")
            
            # 6. Авторизация второго пользователя
            print("\n6. Авторизация Bob...")
            response = requests.post(f"{BASE_URL}/api/users/login", json=user2_data)
            print_response(response, "Авторизация Bob")
            
            if response.status_code == 200:
                bob_token = response.json()["token"]
                print(f"✅ Токен Bob получен: {bob_token[:20]}...")
                
                # 7. Попытка Bob удалить объявление Alice
                print("\n7. Попытка Bob удалить чужое объявление...")
                headers_bob = {"Authorization": f"Bearer {bob_token}"}
                response = requests.delete(
                    f"{BASE_URL}/api/advertisements/{ad_id}", 
                    headers=headers_bob
                )
                print_response(response, "Bob пытается удалить объявление Alice")
                
                # 8. Alice редактирует свое объявление
                print("\n8. Alice редактирует свое объявление...")
                update_data = {
                    "title": "Продам телефон (новая цена)",
                    "description": "iPhone 15 Pro - цена снижена!"
                }
                response = requests.put(
                    f"{BASE_URL}/api/advertisements/{ad_id}",
                    json=update_data,
                    headers=headers
                )
                print_response(response, "Alice обновляет объявление")
                
                # 9. Alice удаляет свое объявление
                print("\n9. Alice удаляет свое объявление...")
                response = requests.delete(
                    f"{BASE_URL}/api/advertisements/{ad_id}",
                    headers=headers
                )
                print_response(response, "Alice удаляет объявление")
                
                # 10. Выход Alice
                print("\n10. Выход Alice из системы...")
                response = requests.post(f"{BASE_URL}/api/users/logout", headers=headers)
                print_response(response, "Logout Alice")
                
                # 11. Попытка использовать старый токен
                print("\n11. Попытка использовать старый токен после выхода...")
                response = requests.post(
                    f"{BASE_URL}/api/advertisements",
                    json=ad_data,
                    headers=headers
                )
                print_response(response, "Использование старого токена")


def test_validation():
    """Тестирование валидации"""
    print("\n\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ВАЛИДАЦИИ")
    print("=" * 60)
    
    # 1. Создание объявления без обязательных полей
    print("\n1. Создание объявления без title...")
    ad_data = {
        "description": "Описание без названия",
        "owner": "user123"
    }
    response = requests.post(f"{BASE_URL}/api/advertisements", json=ad_data)
    print_response(response, "Объявление без title")
    
    # 2. Создание объявления без данных
    print("\n2. Создание объявления без данных...")
    response = requests.post(f"{BASE_URL}/api/advertisements")
    print_response(response, "Объявление без данных")
    
    # 3. Получение несуществующего объявления
    print("\n3. Получение несуществующего объявления...")
    response = requests.get(f"{BASE_URL}/api/advertisements/nonexistent-id")
    print_response(response, "Несуществующее объявление")


def check_server():
    """Проверка доступности сервера"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Сервер доступен")
            print(f"Status: {response.json()}")
            return True
        else:
            print("❌ Сервер вернул неожиданный код")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу")
        print(f"Убедитесь, что сервер запущен на {BASE_URL}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ REST API ДЛЯ ОБЪЯВЛЕНИЙ")
    print("=" * 60)
    
    if not check_server():
        print("\n⚠️  Запустите сервер командой:")
        print("   python app.py  (для базовой версии)")
        print("   python app_with_auth.py  (для версии с авторизацией)")
        exit(1)
    
    # Выбор режима тестирования
    print("\nВыберите режим тестирования:")
    print("1 - Базовое API (app.py)")
    print("2 - API с авторизацией (app_with_auth.py)")
    print("3 - Тестирование валидации")
    print("4 - Все тесты")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        test_basic_api()
    elif choice == "2":
        test_auth_api()
    elif choice == "3":
        test_validation()
    elif choice == "4":
        test_basic_api()
        test_auth_api()
        test_validation()
    else:
        print("❌ Неверный выбор")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
