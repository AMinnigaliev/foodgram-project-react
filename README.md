https://github.com/AMinnigaliev/foodgram-project-react/actions/workflows/main.yml/badge.svg

# Проект Foodgram

## Описание

«Фудграм» — сайтом, на котором пользователи будут публиковать рецепты, 
добавлять чужие рецепты в избранное и подписываться на публикации других 
авторов. Пользователям сайта также будет доступен сервис «Список покупок». 
Он позволит создавать список продуктов, которые нужно купить для приготовления 
выбранных блюд.

## Применяемые технологии

- **Язык программирования:** Python 3.10
- **Фреймворк для веб-разработки:** Django 5.0
- **Фреймворк для создания веб-API:** Django REST Framework 3.15
- **База данных:** PostgreSQL
- **Фронтенд:** HTML, CSS, JavaScript
- **Контейнеризация:** Docker
- **Управление многоконтейнерными приложениями:** Docker Compose
- **Система контроля версий:** Git

## Как развернуть проект

1. Установите Docker и Docker Compose для Linux на сервере
2. Скопируйте на сервер в директорию ***foodgram*** файл ***docker-compose.
   production.yml***
3. Создайте файл ***.env*** на сервере в директории ***foodgram***
4. В директории foodgram выполните команду `sudo docker compose -f 
   docker-compose.production.yml up -d`
5. Выполните миграции, соберите статические файлы бэкенда и скопируйте их в 
   ***/backend_static/static/***:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
PS: *Проект настроен на порт ***8800****

Содержание файл ***.env***:
- POSTGRES_DB - имя базы данных (для PostgreSQL. необязательный, при 
  отсутствии принимает значение *django*)
- POSTGRES_USER - имя пользователя (для PostgreSQL. необязательный, при 
  отсутствии принимает значение *django*)
- POSTGRES_PASSWORD - пароль пользователя (для PostgreSQL)
- DB_HOST - адрес, по которому Django будет соединяться с базой данных (для 
  PostgreSQL)
- DB_PORT - порт, по которому Django будет обращаться к базе данных (для 
  PostgreSQL. необязательный, при отсутствии принимает значение *5432*)
- SECRET_KEY - параметр SECRET_KEY для настройки Django (необязательный, 
  при отсутствии принимает значение *False*)
- DEBUG - параметр DEBUG для настройки Django (необязательный, 
  при отсутствии принимает случайное значение)
- ALLOWED_HOSTS - параметр ALLOWED_HOSTS для настройки Django 
  (необязательный, при отсутствии принимает значение *'127.0.0.1, localhost'*)
- USE_SQLITE - Использовать базу SQLite если значение ***True*** 
  (необязательный, при отсутствии принимает значение *False*)


### Авторы:
- Миннигалиев А.А.
- Яндекс Практикум

адрес сервера: 51.250.21.65:8800
логин: admin
пароль: vfrtyuijn