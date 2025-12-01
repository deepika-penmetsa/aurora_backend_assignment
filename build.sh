set -o errexit

echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"

echo "=== DEBUG INFO ==="
echo "Python path:"
python -c "import sys; print('\n'.join(sys.path))"
echo "Current dir: $(pwd)"
echo "Files:"
ls -la
echo "Search engine files:"
ls -la search_engine/ || echo "No search_engine directory"