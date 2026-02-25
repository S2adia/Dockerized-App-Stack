import os, time, re
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend at a different port during class

DB = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "name": os.getenv("DB_NAME", "appdb"),
    "user": os.getenv("DB_USER", "appuser"),
    "pass": os.getenv("DB_PASS", "changeme123"),
}

def get_conn():
    return psycopg2.connect(
        host=DB["host"], port=DB["port"], dbname=DB["name"],
        user=DB["user"], password=DB["pass"]
    )

def init_db(retries=10):
    for i in range(retries):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS tasks(
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            done BOOLEAN NOT NULL DEFAULT FALSE,
                            created_at TIMESTAMP NOT NULL DEFAULT NOW()
                        );
                        """
                    )
                    conn.commit()
            return
        except Exception as e:
            print(f"[init_db] waiting for db... ({i+1}/{retries}) {e}")
            time.sleep(2)
    raise RuntimeError("DB not ready after retries")

@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

@app.get("/tasks")
def list_tasks():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY id;")
            rows = cur.fetchall()
    return jsonify([
        {"id": r[0], "title": r[1], "done": r[2], "created_at": r[3].isoformat()}
        for r in rows
    ])

@app.post("/tasks")
def add_task():
    data = request.get_json(force=True)
    title = data.get("title")
    if not title: 
        return {"error":"title required"}, 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tasks(title) VALUES (%s) RETURNING id;", (title,))
            new_id = cur.fetchone()[0]
            conn.commit()
    return {"id": new_id, "title": title, "done": False}, 201

@app.get("/security/info")
def security_info():
    uid = os.geteuid() if hasattr(os, "geteuid") else -1
    # detect read-only by trying a write in /
    readonly = True
    try:
        test_path = "/.rw_test"
        with open(test_path, "w") as f: 
            f.write("x")
        os.remove(test_path)
        readonly = False
    except Exception:
        readonly = True

    caps = {"NoNewPrivs": None, "CapEff": None}
    try:
        with open("/proc/self/status") as f:
            s = f.read()
        m = re.search(r"NoNewPrivs:\s(\d+)", s); 
        caps["NoNewPrivs"] = m.group(1) if m else None
        m = re.search(r"CapEff:\s([0-9A-Fa-fx]+)", s); 
        caps["CapEff"] = m.group(1) if m else None
    except Exception as e:
        caps["error"] = str(e)

    return jsonify({
        "uid": uid,
        "readonly": readonly,
        "caps": caps,
        "env": {"HOSTNAME": os.getenv("HOSTNAME", "")}
    })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
