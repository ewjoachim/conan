#!/bin/sh
set -e

# Apply migrations, then hand off to granian as PID 1 (exec = no shell middleman,
# so signals reach the server cleanly).
python manage.py migrate --noinput
exec granian --interface wsgi --host 0.0.0.0 --port 8000 conan.wsgi:application
