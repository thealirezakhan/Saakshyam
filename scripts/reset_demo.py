"""Reset the running demo to its initial state.

Calls the backend's admin reset endpoint (drops and reseeds the demo tenant).
Start the backend first, then run:  python scripts/reset_demo.py
"""

import sys

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
ACCOUNTS = [
    ("sysadmin@aicte.demo", "demo1234"),
    ("admin@northstar.edu.in", "demo1234"),
]


def main() -> int:
    for email, password in ACCOUNTS:
        try:
            login = httpx.post(f"{BASE}/auth/login",
                               json={"email": email, "password": password}, timeout=5)
        except httpx.HTTPError as exc:
            print(f"Backend not reachable at {BASE}. Start it first.\n{exc}")
            return 1
        if login.status_code != 200:
            continue
        token = login.json()["token"]
        res = httpx.post(f"{BASE}/admin/reset-demo",
                         headers={"Authorization": f"Bearer {token}"}, timeout=30)
        print(res.status_code, res.json())
        return 0 if res.status_code == 200 else 1
    print("Could not authenticate a demo admin account.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
