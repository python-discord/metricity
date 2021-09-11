set -e

python create_metricity_db.py
alembic upgrade head

shopt -s nocasematch
if [ "${USE_METRICITY:-true}" = "true" ]; then
    poetry run start
fi
