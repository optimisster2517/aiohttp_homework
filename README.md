# REST API для сайта объявлений на aiohttp

Домашнее задание по aiohttp - REST API для управления объявлениями.

## 📁 Структура проекта

- `aiohttp_app.py` - базовая версия (Задание 1)
- `aiohttp_app_with_auth.py` - расширенная версия с авторизацией (Задание 2)
- `requirements.txt` - зависимости проекта
- `Dockerfile` - конфигурация Docker
- `docker-compose.yml` - конфигурация Docker Compose

## 🚀 Установка и запуск

### 1. Установите зависимости:

```bash
pip install -r requirements.txt
```

### 2. Запустите сервер:

**Базовая версия (без авторизации):**
```bash
python aiohttp_app.py
```

**Версия с авторизацией:**
```bash
python aiohttp_app_with_auth.py
```

Сервер запустится на `http://localhost:8080`

### 3. Docker запуск:

**Запуск базовой версии:**
```bash
docker build -t aiohttp-api .
docker run -p 8080:8080 aiohttp-api
```

**Или с помощью docker-compose:**
```bash
# Базовая версия на порту 8080
docker-compose up aiohttp-basic

# Версия с авторизацией на порту 8081
docker-compose up aiohttp-auth
```

## 📚 API Endpoints

### Базовая версия (aiohttp_app.py)

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

### Версия с авторизацией (aiohttp_app_with_auth.py)

#### Регистрация пользователя
```http
POST /api/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
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

#### Обновить/удалить объявление (только владелец)
```http
PUT /api/advertisements/{ad_id}
Authorization: Bearer your-auth-token
Content-Type: application/json

{
  "title": "Новое название",
  "description": "Новое описание"
}
```

```http
DELETE /api/advertisements/{ad_id}
Authorization: Bearer your-auth-token
```

## 🧪 Примеры использования (curl)

### Базовая версия

```bash
# Создать объявление
curl -X POST http://localhost:8080/api/advertisements \
  -H "Content-Type: application/json" \
  -d '{"title":"Продам ноутбук","description":"MacBook Pro 2020","owner":"Ivan"}'

# Получить все объявления
curl http://localhost:8080/api/advertisements

# Получить конкретное объявление
curl http://localhost:8080/api/advertisements/{ad_id}

# Обновить объявление
curl -X PUT http://localhost:8080/api/advertisements/{ad_id} \
  -H "Content-Type: application/json" \
  -d '{"title":"Продам ноутбук (срочно)","description":"Цена снижена!"}'

# Удалить объявление
curl -X DELETE http://localhost:8080/api/advertisements/{ad_id}
```

### Версия с авторизацией

```bash
# Регистрация
curl -X POST http://localhost:8080/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@mail.com","password":"mypassword"}'

# Авторизация
curl -X POST http://localhost:8080/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@mail.com","password":"mypassword"}'

# Сохраните полученный token!

# Создать объявление (с токеном)
curl -X POST http://localhost:8080/api/advertisements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title":"Продам телефон","description":"iPhone 15 Pro"}'
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

## 📝 HTTP коды ответов

- `200 OK` - успешный запрос
- `201 Created` - ресурс создан
- `400 Bad Request` - некорректные данные
- `401 Unauthorized` - требуется авторизация
- `403 Forbidden` - нет прав доступа
- `404 Not Found` - ресурс не найден
- `409 Conflict` - конфликт (например, пользователь уже существует)

## 🐳 Проверка работы Docker контейнера

1. **Запустите контейнер:**
```bash
docker-compose up aiohttp-basic
```

2. **Проверьте работу роута:**
```bash
curl http://localhost:8080/api/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "advertisements_count": 0
}
```
