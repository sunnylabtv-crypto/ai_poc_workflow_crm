# salesforce_lead_create.py - Lead 생성 예제 (기존 Access Token 사용)
import json
import requests

# test4.py에서 성공적으로 획득한 Access Token 직접 사용
def get_salesforce_credentials():
    """test4.py에서 성공한 토큰 정보 사용"""
    return {
        "access_token": "00DgL00000BTOiD!AQEAQN0lK8w6GXoyINi5gBabqULrdJjPNxSBcJiBG8MwSCtu01EQErn_Qp0idwowXvMImEVObQQ0AGmm6vQBRflqBaxmBefz",
        "instance_url": "https://orgfarm-ed138d457e-dev-ed.develop.my.salesforce.com"
    }

def create_lead(access_token, instance_url, lead_data):
    """Salesforce Lead 생성"""
    
    # Lead 생성 API 엔드포인트
    lead_url = f"{instance_url}/services/data/v60.0/sobjects/Lead/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(lead_url, headers=headers, json=lead_data)
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Lead 생성 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def main():
    """메인 실행 함수"""
    print("Salesforce Lead 생성 시작...")
    
    # 1. 기존 성공한 Access Token 사용
    credentials = get_salesforce_credentials()
    access_token = credentials["access_token"]
    instance_url = credentials["instance_url"]
    
    print(f"✅ 기존 토큰 사용")
    print(f"   Instance URL: {instance_url}")
    
    # 2. Lead 데이터 정의 (Country 필드 제거)
    lead_data = {
        "FirstName": "홍",
        "LastName": "길동",
        "Company": "테스트 회사",
        "Email": "hong.gildong@test.com",
        "Phone": "02-1234-5678",
        "Title": "마케팅 매니저",
        "LeadSource": "Web",
        "Status": "Open - Not Contacted",
        # Country 관련 필드들 제거
        "Industry": "Technology",
        "Rating": "Hot",
        "Description": "JWT Bearer Flow 테스트를 통해 생성된 Lead입니다."
    }
    
    # 3. Lead 생성
    print(f"\nLead 생성 중...")
    print(f"고객 정보: {lead_data['FirstName']} {lead_data['LastName']} ({lead_data['Company']})")
    
    result = create_lead(access_token, instance_url, lead_data)
    
    if result:
        print(f"✅ Lead 생성 성공!")
        print(f"   Lead ID: {result['id']}")
        print(f"   Lead URL: {instance_url}/lightning/r/Lead/{result['id']}/view")
        
        # 생성된 Lead 정보 확인
        verify_lead(access_token, instance_url, result['id'])
        
    else:
        print(f"❌ Lead 생성 실패")

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
        print(f"\n📋 생성된 Lead 정보:")
        print(f"   이름: {lead_info.get('Name', 'N/A')}")
        print(f"   회사: {lead_info.get('Company', 'N/A')}")
        print(f"   이메일: {lead_info.get('Email', 'N/A')}")
        print(f"   전화번호: {lead_info.get('Phone', 'N/A')}")
        print(f"   상태: {lead_info.get('Status', 'N/A')}")
        print(f"   생성일: {lead_info.get('CreatedDate', 'N/A')}")
    else:
        print(f"⚠️ Lead 정보 확인 실패: {response.status_code}")

if __name__ == "__main__":
    main()