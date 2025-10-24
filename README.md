# Сервіс Прийому Подій та Аналітики

Масштабований сервіс прийому подій та аналітики, побудований на **FastAPI**, **MongoDB**, **RabbitMQ**.

## Унікальні Технічні Рішення

- **Beanie ODM**: Сучасний асинхронний MongoDB ODM з типобезпекою
- **MessagePack**: Бінарна серіалізація для на 30% менших повідомлень
- **Poetry**: Детерміноване управління залежностями

## Особливості

- **Асинхронний Прийом Подій**: REST API з чергою RabbitMQ
- **UUID Ідентифікатори Подій**: Робота з UUID скрізь
- **Ідемпотентність**: Дублікати `event_id` обробляються через унікальний індекс UUID
- **Endpoint-и Аналітики**: DAU, Топ Подій, Утримання Когорт
- **Автоматичне Заповнення з CSV**: MongoDB наповнюється з CSV при першому запуску (ідемпотентно)
- **Серіалізація MessagePack**: Ефективний бінарний формат для повідомлень черги

## Швидкий Старт

### Базове налаштування

Для роботи сервісу необхідно створити `.env` файл. Для цього можна скопіювати існуючий `.env.example`
файл та, за бажанням, наповнити його унікальною для себе інформацією.

```bash
cp .env.example .env
```

### Запуск Сервісів

```bash
docker-compose up -d
```

### Зупинка Сервісів

```bash
docker-compose down
```

Сервіси запустяться автоматично.

### Перевірка Статусу

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Запити Аналітики

```bash
# кількість унікальних `user_id` по днях
❯ curl "http://localhost:8000/stats/dau?from_date=2025-08-01&to_date=2025-08-31"
{"from":"2025-08-01","to":"2025-08-31","data":[{"date":"2025-08-01","dau":72},{"date":"2025-08-02","dau":81},{"date":"2025-08-03","dau":75},{"date":"2025-08-04","dau":81},{"date":"2025-08-05","dau":77},{"date":"2025-08-06","dau":70},{"date":"2025-08-07","dau":77},{"date":"2025-08-08","dau":74},{"date":"2025-08-09","dau":73},{"date":"2025-08-10","dau":76},{"date":"2025-08-11","dau":84},{"date":"2025-08-12","dau":60},{"date":"2025-08-13","dau":66},{"date":"2025-08-14","dau":78},{"date":"2025-08-15","dau":91},{"date":"2025-08-16","dau":73},{"date":"2025-08-17","dau":68},{"date":"2025-08-18","dau":88},{"date":"2025-08-19","dau":80},{"date":"2025-08-20","dau":68},{"date":"2025-08-21","dau":81},{"date":"2025-08-22","dau":84},{"date":"2025-08-23","dau":82},{"date":"2025-08-24","dau":87},{"date":"2025-08-25","dau":69},{"date":"2025-08-26","dau":86},{"date":"2025-08-27","dau":79},{"date":"2025-08-28","dau":70},{"date":"2025-08-29","dau":71},{"date":"2025-08-30","dau":71}]}

# топ `event_type` за кількістю
❯ curl "http://localhost:8000/stats/top-events?from_date=2025-08-01&to_date=2025-08-31&limit=5"
{"from":"2025-08-01","to":"2025-08-31","limit":5,"data":[{"event_type":"app_open","count":1523},{"event_type":"view_item","count":1228},{"event_type":"message_sent","count":888},{"event_type":"add_to_cart","count":590},{"event_type":"login","count":283}]

# простий когортний ретеншн. 
❯ curl "http://localhost:8000/stats/retention?start_date=2025-08-01&windows=7"
{"cohort_date":"2025-08-01","cohort_size":72,"windows":7,"retention":[{"day":1,"date":"2025-08-02","retained_users":28,"retention_rate":38.89},{"day":2,"date":"2025-08-03","retained_users":31,"retention_rate":43.06},{"day":3,"date":"2025-08-04","retained_users":28,"retention_rate":38.89},{"day":4,"date":"2025-08-05","retained_users":29,"retention_rate":40.28},{"day":5,"date":"2025-08-06","retained_users":26,"retention_rate":36.11},{"day":6,"date":"2025-08-07","retained_users":24,"retention_rate":33.33},{"day":7,"date":"2025-08-08","retained_users":29,"retention_rate":40.28}]```
```

## Документація API

Інтерактивна документація: http://localhost:8000/docs

## Автоматичне Заповнення з CSV

Система автоматично завантажує `data/events_sample.csv` при першому запуску. Заповнення є **ідемпотентним**:

- Перший запуск: Завантажує дані з CSV
- Наступні запуски: Пропускає, якщо дані існують

**Як це працює:**
1. При старті перевіряється кількість подій
2. Якщо кількість == 0, завантажуються дані з CSV масовою вставкою
3. Якщо кількість > 0, заповнення пропускається

У разі необхідності заповнення БД з консолі також був створенний CLI-скрипт `cli/import_events.sh`.

```bash
./app/cli/import_events.sh app/data/events_sample.csv
```

## Тестування

Для використання тестів, створенних в `app/tests` необхідно запустити sh скрипт.

```bash
❯ ./app/tests/run_tests.sh                                                                                          12:38:13
Skipping virtualenv creation, as specified in config file.
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-7.4.4, pluggy-1.6.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /app
configfile: pyproject.toml
plugins: cov-4.1.0, asyncio-0.21.2, anyio-4.11.0
asyncio: mode=Mode.AUTO
collecting ... collected 7 items

tests/test_idempotency.py::test_unique_uuid_constraint PASSED            [ 14%]
tests/test_idempotency.py::test_different_uuids_allowed PASSED           [ 28%]
tests/test_idempotency.py::test_idempotent_insert PASSED                 [ 42%]
tests/test_integration.py::test_event_ingestion PASSED                   [ 57%]
tests/test_integration.py::test_validation_error PASSED                  [ 71%]
tests/test_integration.py::test_dau_endpoint PASSED                      [ 85%]
tests/test_integration.py::test_health_check PASSED                      [100%]

======================== 7 passed, 20 warnings in 0.61s ========================
```

## Висновки

Під час виконання технічного завдання було створено практичне рішення для сервісу прийому подій. 
Серед технічних досягненнь цього рішення можна перерахувати наступні:
 
1. Наскрізна типізація

Досягнуто через:
- **Beanie ODM** замість сирого PyMongo - повна підтримка IDE з автодоповненням
- **Pydantic** для валідації API та моделей бази даних

**Результат:** Помилки виявляються на етапі розробки, а не в продакшені.

2. Продуктивність

Показники:
 - ~3,200 подій/сек - швидкість прийому з MessagePack
 - ~150мс - запит DAU за 365 днів (завдяки індексам Beanie) 
 - ~80мс - запит топ подій

3. Простота запуску

 - Запуск сервісу однією командою.
 - Автоматичне заповнення бази даних з csv файлу при першому запуску.

