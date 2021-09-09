set -e

python create_metricity_db.py
alembic upgrade head

shopt -s nocasematch
if [ "$skip_metricity" != "true" ]; then
    poetry run start
fi
