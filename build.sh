pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py setup_google --domain carpooling-c5sr.onrender.com
