set -o errexit

python -m pip install --upgrade pip

pip install -r requirements.txt

python manage.py migrate

python manage.py collectstatic --noinput

echo "Checking project structure..."
find . -name "wsgi.py" -type f