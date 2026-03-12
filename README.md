# IT Inventory (Django)

## Setup

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env` and fill in values.
3. Run migrations and start the server:

```powershell
cd config
python manage.py migrate
python manage.py runserver
```

## Environment variables

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (0/1)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

