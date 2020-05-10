del game\migrations\*.py
copy NUL game\migrations\__init__.py
del ground\migrations\*.py
copy NUL ground\migrations\__init__.py

del db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py create groups users state