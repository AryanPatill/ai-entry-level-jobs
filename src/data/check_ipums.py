"""Phase 2 check: can we reach the IPUMS API with our key and CPS registration?

Read-only: lists recent CPS extracts, submits nothing. Never prints the key.
Run from the repo root:  python -m src.data.check_ipums
"""
import requests

from src.utils.config import get_secret

URL = "https://api.ipums.org/extracts"
PARAMS = {"collection": "cps", "version": 2, "limit": 5}

# What each HTTP status most likely means for us
MEANINGS = {
    200: "OK: key is valid and the account can use IPUMS CPS via the API.",
    401: "Unauthorized: the key was rejected. Check for typos or extra spaces in .env.",
    403: "Forbidden: the key works, but the account may not be registered for IPUMS CPS.",
    429: "Rate limited: too many requests. Wait a minute and retry.",
}


def check_connection() -> bool:
    headers = {"Authorization": get_secret("IPUMS_API_KEY")}
    resp = requests.get(URL, params=PARAMS, headers=headers, timeout=30)

    print(f"HTTP status: {resp.status_code}")
    print(MEANINGS.get(resp.status_code, "Unexpected status; see the response body below."))

    if resp.status_code != 200:
        # Error bodies are short messages from IPUMS; they never contain our key.
        print("Response body:", resp.text[:500])
        return False

    body = resp.json()
    extracts = body.get("data", body) if isinstance(body, dict) else body
    print(f"Recent CPS extracts on this account: {len(extracts)}")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if check_connection() else 1)