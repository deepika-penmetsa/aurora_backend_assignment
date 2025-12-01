set -o errexit

echo "=== DEBUG: Checking project structure ==="
pwd
ls -la
echo "Search engine directory:"
ls -la search_engine/ || echo "No search_engine dir"
echo "=== END DEBUG ==="

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo "Build completed!"