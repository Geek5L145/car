# Быстрый старт

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Настройка базы данных

Создайте базу данных PostgreSQL:

```sql
CREATE DATABASE fleet_db;
```

## 3. Настройка переменных окружения

Создайте файл `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/fleet_db
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 4. Заполнение базы данных

```bash
python seed_data.py
```

Это создаст:
- 4 пользователя (admin, mechanic1, driver1, driver2)
- 15 транспортных средств
- Историю ТО за последние 2 года
- Журнал пробега
- Активные и завершенные ремонты

## 5. Запуск приложения

```bash
python run.py
```

Приложение будет доступно по адресу: http://localhost:5000

## Вход в систему

- **Администратор**: `admin` / `password123`
- **Механик**: `mechanic1` / `password123`
- **Водитель**: `driver1` / `password123`

## Основные страницы

- `/dashboard` - Главная страница со статистикой
- `/vehicles` - Реестр транспортных средств
- `/maintenance` - Календарь ТО
- `/predictions` - Прогнозы следующего ТО
- `/notifications` - Уведомления
- `/reports` - Отчеты и экспорт данных


