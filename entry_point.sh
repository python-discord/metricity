set -e

python create_metricity_db.py
alembic upgrade head

shopt -s nocasematch
if [ "$SKIP_METRICITY" != "true" ]; then
    poetry run start
fi
