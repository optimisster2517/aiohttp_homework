# REST API для сайта объявлений

Домашнее задание по Flask - REST API для управления объявлениями.

## 📁 Структура проекта

- `app.py` - базовая версия (Задание 1)
- `app_with_auth.py` - расширенная версия с авторизацией (Задание 2)
- `requirements.txt` - зависимости проекта
- `test_api.py` - примеры тестирования API

## 🚀 Установка и запуск

### 1. Установите зависимости:

```bash
pip install -r requirements.txt
```

### 2. Запустите сервер:

**Базовая версия (без авторизации):**
```bash
python app.py
```

**Версия с авторизацией:**
```bash
python app_with_auth.py
```

Сервер запустится на `http://localhost:5000`

## 📚 API Endpoints

### Базовая версия (app.py)

#### Создать объявление
```http
POST /api/advertisements
Content-Type: application/json

{
  "title": "Продам велосипед",
  "description": "Горный велосипед в отличном состоянии",
  "owner": "user123"
}
```

#### Получить объявление
```http
GET /api/advertisements/{ad_id}
```

#### Получить все объявления
```http
GET /api/advertisements
```

#### Обновить объявление
```http
PUT /api/advertisements/{ad_id}
Content-Type: application/json

{
  "title": "Продам велосипед (обновлено)",
  "description": "Новое описание"
}
```

#### Удалить объявление
```http
DELETE /api/advertisements/{ad_id}
```

---

### Версия с авторизацией (app_with_auth.py)

#### Регистрация пользователя
```http
POST /api/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Ответ:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "created_at": "2025-02-06T10:30:00"
}
```

#### Авторизация
```http
POST /api/users/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Ответ:**
```json
{
  "token": "your-auth-token",
  "user_id": "user-uuid",
  "email": "user@example.com"
}
```

#### Создать объявление (требуется авторизация)
```http
POST /api/advertisements
Authorization: Bearer your-auth-token
Content-Type: application/json

{
  "title": "Продам велосипед",
  "description": "Горный велосипед в отличном состоянии"
}
```

#### Обновить объявление (только владелец)
```http
PUT /api/advertisements/{ad_id}
Authorization: Bearer your-auth-token
Content-Type: application/json

{
  "title": "Новое название",
  "description": "Новое описание"
}
```

#### Удалить объявление (только владелец)
```http
DELETE /api/advertisements/{ad_id}
Authorization: Bearer your-auth-token
```

#### Выход
```http
POST /api/users/logout
Authorization: Bearer your-auth-token
```

## 🧪 Примеры использования (curl)

### Базовая версия

```bash
# Создать объявление
curl -X POST http://localhost:5000/api/advertisements \
  -H "Content-Type: application/json" \
  -d '{"title":"Продам ноутбук","description":"MacBook Pro 2020","owner":"Ivan"}'

# Получить все объявления
curl http://localhost:5000/api/advertisements

# Получить конкретное объявление
curl http://localhost:5000/api/advertisements/{ad_id}

# Обновить объявление
curl -X PUT http://localhost:5000/api/advertisements/{ad_id} \
  -H "Content-Type: application/json" \
  -d '{"title":"Продам ноутбук (срочно)","description":"Цена снижена!"}'

# Удалить объявление
curl -X DELETE http://localhost:5000/api/advertisements/{ad_id}
```

### Версия с авторизацией

```bash
# Регистрация
curl -X POST http://localhost:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@mail.com","password":"mypassword"}'

# Авторизация
curl -X POST http://localhost:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@mail.com","password":"mypassword"}'

# Сохраните полученный token!

# Создать объявление (с токеном)
curl -X POST http://localhost:5000/api/advertisements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title":"Продам телефон","description":"iPhone 15 Pro"}'

# Обновить объявление (с токеном)
curl -X PUT http://localhost:5000/api/advertisements/{ad_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title":"Продам телефон (новая цена)"}'

# Удалить объявление (с токеном)
curl -X DELETE http://localhost:5000/api/advertisements/{ad_id} \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📊 Структура данных

### Объявление (Advertisement)
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "created_at": "ISO datetime",
  "owner": "user_id"
}
```

### Пользователь (User)
```json
{
  "id": "uuid",
  "email": "string",
  "password_hash": "string",
  "created_at": "ISO datetime"
}
```

## 🔒 Система прав доступа (Задание 2)

- ✅ Создавать объявления могут только авторизованные пользователи
- ✅ Редактировать объявление может только его владелец
- ✅ Удалять объявление может только его владелец
- ✅ Просматривать объявления могут все пользователи

## ⚠️ Важные замечания

1. **Хранение данных**: В текущей реализации используется словарь Python для хранения данных в памяти. При перезапуске сервера все данные будут потеряны. Для продакшена используйте базу данных (SQLite, PostgreSQL, MongoDB).

2. **Безопасность паролей**: Реализовано хеширование паролей с использованием SHA-256 и соли. В продакшене рекомендуется использовать более надежные методы (bcrypt, argon2).

3. **Токены**: Используются простые токены в памяти. Для продакшена рекомендуется JWT (JSON Web Tokens).

4. **Валидация**: Добавлена базовая валидация. Можно расширить с помощью библиотек типа marshmallow или pydantic.

## 🎯 Что реализовано

### Задание 1 ✅
- [x] POST метод для создания объявления
- [x] GET метод для получения объявления
- [x] DELETE метод для удаления объявления
- [x] PUT/PATCH методы для редактирования
- [x] Все требуемые поля (заголовок, описание, дата создания, владелец)

### Задание 2 ✅ (необязательное)
- [x] Регистрация пользователей
- [x] Авторизация с токенами
- [x] Хеширование паролей
- [x] Проверка прав доступа
- [x] Создание только для авторизованных
- [x] Редактирование/удаление только для владельца

## 📝 HTTP коды ответов

- `200 OK` - успешный запрос
- `201 Created` - ресурс создан
- `400 Bad Request` - некорректные данные
- `401 Unauthorized` - требуется авторизация
- `403 Forbidden` - нет прав доступа
- `404 Not Found` - ресурс не найден
- `409 Conflict` - конфликт (например, пользователь уже существует)

