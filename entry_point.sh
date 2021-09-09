set -e
python create_metricity_db.py
alembic upgrade head
if [ -z "$skip_metricity" ]; then
    poetry run start
fi
