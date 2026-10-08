"""
Auto-login script for Sophos captive portal (college wifi).

CONFIRMED FROM YOUR NETWORK TAB:
- Login endpoint:  https://192.168.200.1:8090/login.xml
  Payload: mode=191, username, password, a (timestamp), producttype=0
- Logout endpoint: https://192.168.200.1:8090/logout.xml
  Payload: mode=193, username, a (timestamp), producttype=0
- Connectivity check: http://connectivitycheck.gstatic.com/generate_204
  204 = logged in, 200 = logged out (verified on this network)

HOW TO USE:
1. Fill in USERNAME and PASSWORD below.
2. Install requests: pip install requests
3. Run: python wifi_autologin.py
4. Leave it running (see notes at bottom for auto-start options).

SECURITY NOTE: This talks to the gateway over plain HTTP (confirmed via
browser DevTools, not HTTPS as originally assumed) - credentials are sent
unencrypted on your local network segment, same as they are when you log
in via browser through this portal. Only run this while connected to your
college network.
"""

import requests
import time

# --- CONFIG ---

LOGIN_URL = "http://192.168.200.1:8090/login.xml"
LOGOUT_URL = "http://192.168.200.1:8090/logout.xml"

USERNAME = "student"       # <-- replace with your actual username
PASSWORD = "student@123"   # <-- replace with your actual password

# Google's captive-portal detection endpoint. Returns 204 when the request
# reaches Google untouched (you're logged in). Returns 200 (with Sophos's
# own HTML) when Sophos intercepts it (you're logged out / session expired).
CHECK_URL = "http://connectivitycheck.gstatic.com/generate_204"

# How often to check if you're still connected (seconds)
CHECK_INTERVAL = 0.5

# ----------------------------------------------------------------


def build_login_payload():
    return {
        "mode": "191",
        "username": USERNAME,
        "password": PASSWORD,
        "a": str(int(time.time() * 1000)),  # fresh timestamp every call
        "producttype": "0",
    }


def build_logout_payload():
    return {
        "mode": "193",
        "username": USERNAME,
        "a": str(int(time.time() * 1000)),
        "producttype": "0",
    }


def is_connected():
    """
    Google's connectivity-check endpoint returns 204 when the request
    reaches Google untouched. If Sophos has intercepted the connection
    (session expired), it returns its own page instead - confirmed on
    this network to come back as 200.
    """
    try:
        r = requests.get(CHECK_URL, timeout=10)
        return r.status_code == 204
    except requests.RequestException:
        return False


def login():
    headers = {
        "Referer": "http://192.168.200.1:8090/httpclient.html",
        "Origin": "http://192.168.200.1:8090",
    }
    try:
        session = requests.Session()
        # Load the portal page first (matches real browser behavior)
        session.get("http://192.168.200.1:8090/httpclient.html", timeout=10)
        r = session.post(LOGIN_URL, data=build_login_payload(), headers=headers, timeout=10)
        success = "LIVE" in r.text
        print(f"Login attempt -> HTTP {r.status_code} | Success: {success}")
        print(f"Response: {r.text.strip()}")
        return success
    except requests.RequestException as e:
        print(f"Login request failed: {e}")
        return False


def logout():
    headers = {
        "Referer": "http://192.168.200.1:8090/httpclient.html",
        "Origin": "http://192.168.200.1:8090",
    }
    try:
        session = requests.Session()
        session.get("http://192.168.200.1:8090/httpclient.html", timeout=10)
        r = session.post(LOGOUT_URL, data=build_logout_payload(), headers=headers, timeout=10)
        print(f"Logout attempt -> HTTP {r.status_code}")
        print(f"Response: {r.text.strip()}")
        return r.status_code == 200
    except requests.RequestException as e:
        print(f"Logout request failed: {e}")
        return False


def main():
    print(f"Wifi auto-login started. Checking every {CHECK_INTERVAL} seconds.")
    while True:
        if not is_connected():
            print("Not connected (or session expired). Attempting login...")
            login()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
