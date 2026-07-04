# deskflow

IT help desk and ticketing API built with Django REST Framework. Requesters open
tickets, agents work them, and managers handle assignment and SLA breaches.

Work in progress.

## Setup

Requires PostgreSQL and Redis (`docker compose up -d`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set DJANGO_SECRET_KEY and POSTGRES_PASSWORD in .env

python manage.py migrate
python manage.py runserver
```
