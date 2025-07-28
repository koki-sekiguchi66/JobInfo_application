#!/usr/bin/env bash
set -o errexit

echo "=== Build process started ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Database connection test ==="
python -c "
import os
print('DATABASE_URL exists:', 'DATABASE_URL' in os.environ)
if 'DATABASE_URL' in os.environ:
    print('DATABASE_URL value:', os.environ['DATABASE_URL'][:50] + '...')
"

echo "=== Django check ==="
python manage.py check

echo "=== Show migrations status ==="
python manage.py showmigrations || echo "showmigrations failed"

echo "=== Make migrations ==="
python manage.py makemigrations --verbosity=2

echo "=== Run migrations ==="
python manage.py migrate --verbosity=2

echo "=== Final migration status ==="
python manage.py showmigrations

echo "=== Collect static files ==="
python manage.py collectstatic --no-input

echo "=== Build completed ==="