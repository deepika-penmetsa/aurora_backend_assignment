set -o errexit

mkdir -p staticfiles

python manage.py migrate

python manage.py collectstatic --noinput