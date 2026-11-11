import os
import time
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def init_db(retries=10, delay=2):
    for intento in range(1, retries + 1):
        try:
            conn = get_conn()
            try:
                with conn, conn.cursor() as cur:
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS notas ("
                        "id SERIAL PRIMARY KEY, texto TEXT NOT NULL)"
                    )
            finally:
                conn.close()
            print("Base de datos lista", flush=True)
            return
        except psycopg2.OperationalError as e:
            print(f"Intento {intento}/{retries}: BD no disponible ({e})", flush=True)
            time.sleep(delay)
    raise RuntimeError("No se pudo conectar a la base de datos")


init_db()


@app.get("/")
def health():
    return jsonify(status="ok")


@app.post("/notas")
def crear_nota():
    texto = (request.get_json(silent=True) or {}).get("texto")
    if not texto:
        return jsonify(error="Falta el campo 'texto'"), 400
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO notas (texto) VALUES (%s) RETURNING id", (texto,))
            nuevo_id = cur.fetchone()[0]
    finally:
        conn.close()
    return jsonify(id=nuevo_id, texto=texto), 201


@app.get("/notas")
def listar_notas():
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT id, texto FROM notas ORDER BY id")
            filas = [{"id": i, "texto": t} for i, t in cur.fetchall()]
    finally:
        conn.close()
    return jsonify(filas)