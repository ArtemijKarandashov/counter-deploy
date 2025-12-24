import os
import time
from flask import Flask, jsonify, send_from_directory
from redis import Redis, RedisError
from dotenv import load_dotenv
from pathlib import Path
from flask_cors import CORS

# =========================
# Env & app setup
# =========================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD') or None

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'static'),
    static_url_path='/'
)
CORS(app)

r = None
COUNTER_KEY = 'counter:value'


def get_redis_client(retries=5, wait=1):
    for i in range(retries):
        try:
            client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
            )
            client.ping()
            return client
        except RedisError:
            if i == retries - 1:
                raise
            time.sleep(wait)
    raise RedisError("Cannot connect to Redis")


def get_redis():
    global r
    if r is None:
        r = get_redis_client()
    return r


def ensure_counter_exists():
    redis = get_redis()
    if redis.get(COUNTER_KEY) is None:
        redis.set(COUNTER_KEY, 0)


@app.before_request
def before_request():
    ensure_counter_exists()


@app.route('/api/counter', methods=['GET'])
def get_counter():
    try:
        v = int(get_redis().get(COUNTER_KEY) or 0)
        return jsonify({"value": v})
    except Exception:
        return jsonify({"error": "Redis error"}), 500


@app.route('/api/counter/increment', methods=['POST'])
def increment():
    try:
        v = get_redis().incr(COUNTER_KEY)
        return jsonify({"value": int(v)})
    except Exception:
        return jsonify({"error": "Redis error"}), 500


@app.route('/api/counter/decrement', methods=['POST'])
def decrement():
    try:
        v = get_redis().decr(COUNTER_KEY)
        if v < 0:
            get_redis().incr(COUNTER_KEY)
            return jsonify({"error": "Counter cannot be negative"}), 400
        return jsonify({"value": int(v)})
    except Exception:
        return jsonify({"error": "Redis error"}), 500


@app.route('/api/counter/reset', methods=['POST'])
def reset():
    try:
        get_redis().set(COUNTER_KEY, 0)
        return jsonify({"value": 0})
    except Exception:
        return jsonify({"error": "Redis error"}), 500


@app.route('/api/author/', methods=['GET'])
def author():
    return jsonify({"author": "Karandashov Artemij (149920)"})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    static_dir = BASE_DIR / 'static'
    if path != "" and (static_dir / path).exists():
        return send_from_directory(str(static_dir), path)
    return send_from_directory(str(static_dir), 'index.html')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8000))
    )
