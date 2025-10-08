# salesforce_lead_create_complete.py - JWT 토큰 획득부터 Lead 생성까지 완전 버전
import os
import time
import json
import requests
import jwt

def get_salesforce_token():
    """Salesforce JWT Bearer Flow로 Access Token 획득"""
    
    # 설정 (test4.py에서 성공한 값들 사용)
    CONSUMER_KEY = (os.getenv("SF_CLIENT_ID") or "3MVG9dAEux2v1sLvZhbimKhJf3K8v6sUDjD.fKZ2CbvJfBN0SceUvMEkNlHWppQ06_ZNI8fHjZq3ULNO342Ri").strip()
    USERNAME     = (os.getenv("SF_USERNAME")  or "sunnylabtv439@agentforce.com").strip()
    LOGIN_URL    = (os.getenv("SF_LOGIN_URL") or "https://orgfarm-ed138d457e-dev-ed.develop.my.salesforce.com").strip()
    KEY_PATH     = (os.getenv("SF_JWT_KEY")   or r"C:\Temp\sf_new.key").strip()

    print(f"[토큰] JWT 토큰 요청 중...")
    print(f"   Consumer Key: {CONSUMER_KEY[:20]}...")
    print(f"   Username: {USERNAME}")
    print(f"   Login URL: {LOGIN_URL}")

    # 개인키 로드
    try:
        with open(KEY_PATH, "r", encoding="utf-8") as f:
            private_key = f.read().strip()
    except FileNotFoundError:
        raise Exception(f"개인키 파일을 찾을 수 없습니다: {KEY_PATH}")

    # JWT 생성
    now = int(time.time())
    payload = {
        "iss": CONSUMER_KEY,    # Connected App Consumer Key
        "sub": USERNAME,        # Salesforce Username
        "aud": LOGIN_URL,       # My Domain URL
        "iat": now,
        "exp": now + 180        # 3분 이내 권장
    }

    assertion = jwt.encode(payload, private_key, algorithm="RS256")
    if isinstance(assertion, bytes):
        assertion = assertion.decode("utf-8")

    # 토큰 요청
    token_url = f"{LOGIN_URL}/services/oauth2/token"
    resp = requests.post(
        token_url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )

    if resp.status_code == 200:
        token_data = resp.json()
        print(f"✅ JWT 토큰 획득 성공!")
        return token_data
    else:
        raise Exception(f"토큰 요청 실패: {resp.status_code} - {resp.text}")

def create_lead(access_token, instance_url, lead_data):
    """Salesforce Lead 생성"""
    
    # Lead 생성 API 엔드포인트
    lead_url = f"{instance_url}/services/data/v60.0/sobjects/Lead/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"[API] Lead 생성 요청 중...")
    print(f"   URL: {lead_url}")
    print(f"   고객: {lead_data.get('FirstName', '')} {lead_data.get('LastName', '')} ({lead_data.get('Company', '')})")
    
    response = requests.post(lead_url, headers=headers, json=lead_data)
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Lead 생성 실패: {response.status_code}")
        print(f"   응답: {response.text}")
        return None

def verify_lead(access_token, instance_url, lead_id):
    """생성된 Lead 정보 확인"""
    
    lead_url = f"{instance_url}/services/data/v60.0/sobjects/Lead/{lead_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(lead_url, headers=headers)
    
    if response.status_code == 200:
        lead_info = response.json()
        print(f"\n📋 생성된 Lead 정보 확인:")
        print(f"   이름: {lead_info.get('Name', 'N/A')}")
        print(f"   회사: {lead_info.get('Company', 'N/A')}")
        print(f"   이메일: {lead_info.get('Email', 'N/A')}")
        print(f"   전화번호: {lead_info.get('Phone', 'N/A')}")
        print(f"   상태: {lead_info.get('Status', 'N/A')}")
        print(f"   소스: {lead_info.get('LeadSource', 'N/A')}")
        print(f"   생성일: {lead_info.get('CreatedDate', 'N/A')}")
        return lead_info
    else:
        print(f"⚠️ Lead 정보 확인 실패: {response.status_code}")
        return None

def create_multiple_leads(access_token, instance_url):
    """여러 Lead 생성 예제"""
    
    leads_data = [
        {
            "FirstName": "김",
            "LastName": "철수",
            "Company": "ABC 컨설팅",
            "Email": "kim.cheolsu@abc.com",
            "Phone": "02-1111-2222",
            "Title": "부장",
            "LeadSource": "Phone Inquiry",
            "Status": "Open - Not Contacted",
            "Industry": "Consulting",
            "Rating": "Warm",
            "Description": "전화 문의를 통해 접수된 Lead"
        },
        {
            "FirstName": "이",
            "LastName": "영희",
            "Company": "XYZ 기업",
            "Email": "lee.younghee@xyz.co.kr",
            "Phone": "031-3333-4444",
            "Title": "팀장",
            "LeadSource": "Web",
            "Status": "Working - Contacted",
            "Industry": "Manufacturing",
            "Rating": "Hot",
            "Description": "웹사이트를 통해 접수된 Lead"
        },
        {
            "FirstName": "박",
            "LastName": "민수",
            "Company": "DEF 솔루션",
            "Email": "park.minsu@def.net",
            "Phone": "051-5555-6666",
            "Title": "대리",
            "LeadSource": "Trade Show",
            "Status": "Open - Not Contacted",
            "Industry": "Technology",
            "Rating": "Cold",
            "Description": "전시회에서 수집한 명함 정보"
        }
    ]
    
    created_leads = []
    
    for i, lead_data in enumerate(leads_data, 1):
        print(f"\n[{i}/{len(leads_data)}] Lead 생성 중...")
        result = create_lead(access_token, instance_url, lead_data)
        
        if result:
            print(f"✅ Lead 생성 성공: {result['id']}")
            created_leads.append(result['id'])
        else:
            print(f"❌ Lead 생성 실패")
        
        # API 호출 간격 조절
        time.sleep(1)
    
    return created_leads

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("SALESFORCE LEAD 생성 도구")
    print("=" * 60)
    
    # 1. Access Token 획득
    try:
        token_response = get_salesforce_token()
        access_token = token_response["access_token"]
        instance_url = token_response["instance_url"]
        
        print(f"   Instance URL: {instance_url}")
        print(f"   Token Type: {token_response.get('token_type', 'Bearer')}")
        
    except Exception as e:
        print(f"❌ 토큰 획득 실패: {e}")
        return

    # 2. 단일 Lead 생성
    print(f"\n" + "─" * 40)
    print("단일 Lead 생성")
    print("─" * 40)
    
    lead_data = {
        "FirstName": "박",
        "LastName": "경화",  # 다른 이름으로 변경
        "Company": "AI 솔루션",  # 다른 회사명으로 변경
        "Email": "parkkh@aisolution.com",  # 다른 이메일로 변경
        "Phone": "02-1234-5678",  # 다른 전화번호로 변경
        "Title": "과장",
        "LeadSource": "Web",
        "Status": "Open - Not Contacted",
        "Industry": "Technology",
        "Rating": "Hot",
        "Description": "JWT Bearer Flow 테스트를 통해 생성된 새로운 Lead입니다."
    }
    
    result = create_lead(access_token, instance_url, lead_data)
    
    if result:
        print(f"✅ Lead 생성 성공!")
        print(f"   Lead ID: {result['id']}")
        print(f"   Lead URL: {instance_url}/lightning/r/Lead/{result['id']}/view")
        
        # 생성된 Lead 정보 확인
        verify_lead(access_token, instance_url, result['id'])
        
    else:
        print(f"❌ Lead 생성 실패")
        return

    # 3. 여러 Lead 생성 (선택사항)
    print(f"\n" + "─" * 40)
    print("다중 Lead 생성")
    print("─" * 40)
    
    user_input = input("여러 개의 샘플 Lead를 추가로 생성하시겠습니까? (y/n): ").strip().lower()
    
    if user_input == 'y':
        created_leads = create_multiple_leads(access_token, instance_url)
        print(f"\n✅ 총 {len(created_leads)}개의 Lead가 추가로 생성되었습니다.")
        
        for lead_id in created_leads:
            print(f"   - Lead URL: {instance_url}/lightning/r/Lead/{lead_id}/view")
    
    print(f"\n" + "=" * 60)
    print("Lead 생성 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()