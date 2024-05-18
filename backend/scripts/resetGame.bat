del db.sqlite3
python manage.py makemigrations --no-header
python manage.py migrate
python manage.py setupgame %1
