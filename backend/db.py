import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "Autos_Colombia",
    "user": "postgres",
    "password": "postgres"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)
