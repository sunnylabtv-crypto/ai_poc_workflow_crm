# test4.py - Salesforce OAuth 2.0 JWT Bearer Flow
import os
import time
import json
import base64
import requests
import jwt  # pip install pyjwt cryptography requests

# 설정: 환경변수 우선, 없으면 하드코딩 값 사용
CONSUMER_KEY = (os.getenv("SF_CLIENT_ID") or "3MVG9dAEux2v1sLvZhbimKhJf3K8v6sUDjD.fKZ2CbvJfBN0SceUvMEkNlHWppQ06_ZNI8fHjZq3ULNO342Ri").strip()
USERNAME     = (os.getenv("SF_USERNAME")  or "sunnylabtv439@agentforce.com").strip()
LOGIN_URL    = (os.getenv("SF_LOGIN_URL") or "https://orgfarm-ed138d457e-dev-ed.develop.my.salesforce.com").strip()
KEY_PATH     = (os.getenv("SF_JWT_KEY")   or r"C:\Temp\sf_new.key").strip()  # 새로 생성한 키 파일

# 개인키 로드
with open(KEY_PATH, "r", encoding="utf-8") as f:
    private_key = f.read().strip()

# JWT 페이로드
now = int(time.time())
payload = {
    "iss": CONSUMER_KEY,    # Connected App Consumer Key
    "sub": USERNAME,        # Salesforce Username
    "aud": LOGIN_URL,       # My Domain URL
    "iat": now,
    "exp": now + 180        # 3분 이내 권장
}

# JWT 생성 (RS256)
assertion = jwt.encode(payload, private_key, algorithm="RS256")
if isinstance(assertion, bytes):
    assertion = assertion.decode("utf-8")

# 디버그 출력: JWT 본문 확인
def _b64url_json(seg: str):
    seg += "=" * ((4 - len(seg) % 4) % 4)  # padding 보정
    return json.loads(base64.urlsafe_b64decode(seg).decode())

body = _b64url_json(assertion.split(".")[1])
print("[DEBUG] iss:", body.get("iss"))
print("[DEBUG] sub:", body.get("sub"))
print("[DEBUG] aud:", body.get("aud"))
print("[DEBUG] exp-iat (sec):", body.get("exp", 0) - body.get("iat", 0))

token_url = f"{LOGIN_URL}/services/oauth2/token"
print("[DEBUG] token url:", token_url)

# 토큰 요청
resp = requests.post(
    token_url,
    data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=20,
)

print("[RESULT] Status:", resp.status_code)
try:
    response_json = resp.json()
    print("[RESULT] Body:", json.dumps(response_json, indent=2))
    
    # 성공시 access_token 출력
    if resp.status_code == 200 and "access_token" in response_json:
        print("\n✅ JWT 토큰 인증 성공!")
        print(f"Full Access Token: {response_json['access_token']}")  # 전체 토큰 출력
        print(f"Instance URL: {response_json.get('instance_url', 'N/A')}")
        print(f"Token Type: {response_json.get('token_type', 'N/A')}")
    else:
        print(f"\n❌ JWT 토큰 인증 실패:")
        print(f"Error: {response_json.get('error', 'unknown')}")
        print(f"Description: {response_json.get('error_description', 'No description')}")
        
except Exception:
    print("[RESULT] Body:", resp.text)