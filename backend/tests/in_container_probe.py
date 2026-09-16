"""Server-capacity probe run INSIDE the backend container (127.0.0.1)."""
import json
import subprocess
import threading
import time
import urllib.request

base = "http://127.0.0.1:8000"


def login():
    h = {"Content-Type": "application/json"}
    d = json.dumps({"email": "smoke@loadmailx.io", "password": "smokepass1"}).encode()
    req = urllib.request.Request(base + "/api/auth/login", data=d, headers=h)
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def hammer(seconds, token, chat_id, results):
    end = time.monotonic() + seconds
    lat = []
    while time.monotonic() < end:
        t0 = time.perf_counter()
        try:
            d = json.dumps({"conversation_id": str(chat_id), "query": "Detect water bodies", "image_ids": []}).encode()
            req = urllib.request.Request(base + "/api/query", data=d,
                                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
            urllib.request.urlopen(req, timeout=60).read()
            results["ok"] += 1
        except Exception:
            results["err"] += 1
        lat.append((time.perf_counter() - t0) * 1000)
    results["lat"].extend(lat)


def main():
    tok = login()
    cid = get(base + "/api/conversations", tok)[0]["id"]
    print("seeded, chat_id", cid, flush=True)
    for conc in (25, 50, 100, 200, 400):
        res = {"ok": 0, "err": 0, "lat": []}
        threads = [threading.Thread(target=hammer, args=(15, tok, cid, res)) for _ in range(conc)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        lat = sorted(res["lat"])
        n = len(lat)
        p = lambda q: lat[min(n - 1, int(n * q / 100))]
        print(f"conc={conc:>4} ok={res['ok']:>6} err={res['err']:>4} rps={res['ok'] / 15:>6.1f} "
              f"p50={p(50):>7.1f} p95={p(95):>7.1f} p99={p(99):>7.1f} max={lat[-1]:>7.1f}", flush=True)


if __name__ == "__main__":
    main()