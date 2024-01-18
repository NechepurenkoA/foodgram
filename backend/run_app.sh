python manage.py migrate
python manage.py collectstatic --no-input
python manage.py loaddata dump.json
gunicorn -b 0.0.0.0:9090 foodgram.wsgi