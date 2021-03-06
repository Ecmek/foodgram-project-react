# api_foodgram
![foodgram_workflow](https://github.com/ecmek/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# Проект доступен по адресу 

http://foodgrem.co.vu/

## Описание проекта Foodgram
«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты, подписываться на публикации других авторов и добавлять рецепты в избранное. Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Запуск с использованием CI/CD

Установить docker, docker-compose на боевом сервере
```
ssh <username>@<server_ip>
sudo apt install docker.io
https://docs.docker.com/compose/install/ # docker-compose
```
- Заполнить в настройках репозитория секреты согласно env_template.txt
- В docker-compose web:image установить свой контейнер

Скопировать на сервер настройки infra, fronted, docs.
```
scp -r docs/ <username>@<server_ip>:/home/<username>/docs/
scp -r infra/ <username>@<server_ip>:/home/<username>/infra/
scp -r frontend/ <username>@<server_ip>:/home/<username>/frontend/
```

## Запуск проекта через Docker

Собрать контейнер:
- docker-compose up -d

Выполнить следующие команды:
```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate --noinput 
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```
По желанию наполнить бд ингредиентами и тэгами:
```
docker-compose exec web python manage.py load_tags
docker-compose exec web python manage.py load_ingredients
```


## Запуск проекта в dev-режиме

- Установить и активировать виртуальное окружение
- Установить зависимости из файла requirements.txt
```
python -m pip install --upgrade pip

pip install -r requirements.txt
```
- Выполнить миграции:
```
python manage.py migrate
```

- В папке с файлом manage.py выполнить команду:
```
python manage.py runserver
```

- Для загрузки ингредиентов и тэгов:
```
docker-compose exec web python manage.py load_tags
docker-compose exec web python manage.py load_ingredients
```

### Документация к API доступна после запуска
http://127.0.0.1/api/docs/
...
