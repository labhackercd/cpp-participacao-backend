#!/bin/bash

# wait for Postgres to start
postgres_ready(){
python << END
import sys
import psycopg2
import os

try:
    conn = psycopg2.connect(dbname=os.environ["NAME"], user=os.environ["USER"], password=os.environ["PASSWORD"], host="db")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

python3 src/manage.py makemigrations
python3 src/manage.py migrate
python3 src/manage.py runserver 0.0.0.0:8000