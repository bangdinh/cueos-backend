import requests
import time

BASE_URL = "http://127.0.0.1:8888"

# User A logs in
print("User A logging in...")
r1 = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "secret"})
token_A = r1.json()["access_token"]
print("User A token:", token_A[:10])

# User A makes request
r_req1 = requests.get(f"{BASE_URL}/api/reports/hq/overview", headers={"Authorization": f"Bearer {token_A}"})
print("User A request status:", r_req1.status_code)

# User B logs in
print("\nUser B logging in...")
r2 = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "secret"})
token_B = r2.json()["access_token"]
print("User B token:", token_B[:10])

# User B makes request
r_req2 = requests.get(f"{BASE_URL}/api/reports/hq/overview", headers={"Authorization": f"Bearer {token_B}"})
print("User B request status:", r_req2.status_code)

# User A makes request again
r_req3 = requests.get(f"{BASE_URL}/api/reports/hq/overview", headers={"Authorization": f"Bearer {token_A}"})
print("User A request 2 status:", r_req3.status_code)
print("User A request 2 body:", r_req3.text)
