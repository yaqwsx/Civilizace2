del game\migrations\*.py
copy NUL game\migrations\__init__.py
del core\migrations\*.py
copy NUL core\migrations\__init__.py

del db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py setupgame %1
