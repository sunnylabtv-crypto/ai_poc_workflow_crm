# services/salesforce_service_v2.py

from services.base_service import BaseService
import os
import time
import jwt
import requests
from typing import Dict, Optional

class SalesforceServiceV2(BaseService):
    """Salesforce 서비스 (JWT Bearer Flow)"""
    
     # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 이 부분을 수정하세요 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    def __init__(self, config):  # <-- 여기에 config 파라미터를 추가합니다.
        super().__init__("Salesforce")
        
        # 환경변수에서 설정을 가져옵니다.
        sf_config = config['SALESFORCE_CONFIG']
        self.consumer_key = os.getenv(sf_config['CONSUMER_KEY_ENV'])
        self.username = os.getenv(sf_config['USERNAME_ENV'])
        self.login_url = os.getenv("SF_LOGIN_URL")
        self.key_path = os.getenv("SF_JWT_KEY")
        
        self.access_token = None
        self.instance_url = None
        
        self.logger.info("Salesforce 서비스 초기화")
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    
    def authenticate(self) -> bool:
        """Salesforce JWT Bearer Flow로 Access Token 획득"""
        try:
            self.logger.info("Salesforce JWT 토큰 요청 중...")
            
            # 개인키 로드
            try:
                with open(self.key_path, "r", encoding="utf-8") as f:
                    private_key = f.read().strip()
            except FileNotFoundError:
                self.logger.error(f"개인키 파일을 찾을 수 없습니다: {self.key_path}")
                return False
            
            # JWT 생성
            now = int(time.time())
            payload = {
                "iss": self.consumer_key,
                "sub": self.username,
                "aud": self.login_url,
                "iat": now,
                "exp": now + 180
            }
            
            assertion = jwt.encode(payload, private_key, algorithm="RS256")
            if isinstance(assertion, bytes):
                assertion = assertion.decode("utf-8")
            
            # 토큰 요청
            token_url = f"{self.login_url}/services/oauth2/token"
            response = requests.post(
                token_url,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=20,
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.instance_url = token_data["instance_url"]
                
                self.logger.info(f"✅ Salesforce JWT 토큰 획득 성공!")
                self.logger.info(f"   Instance URL: {self.instance_url}")
                return True
            else:
                self.logger.error(f"토큰 요청 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Salesforce 인증 실패: {e}")
            return False
    
    def create_lead(self, customer_info: Dict) -> bool:
        """
        리드 생성
        
        Args:
            customer_info: {
                'name': str,
                'company': str,
                'title': str,
                'phone': str,
                'email': str
            }
        """
        if not self.access_token or not self.instance_url:
            self.logger.error("Salesforce 인증이 필요합니다")
            return False
        
        try:
            # 이름 분리 (성/이름)
            name = customer_info.get('name', '')
            if name:
                name_parts = name.strip().split()
                if len(name_parts) >= 2:
                    last_name = name_parts[0]
                    first_name = ' '.join(name_parts[1:])
                else:
                    last_name = name
                    first_name = ''
            else:
                last_name = 'Unknown'
                first_name = ''
            
            # Lead 데이터 구성
            lead_data = {
                "LastName": last_name,
                "FirstName": first_name,
                "Company": customer_info.get('company', 'Unknown'),
                "Title": customer_info.get('title', ''),
                "Phone": customer_info.get('phone', ''),
                "Email": customer_info.get('email', ''),
                "LeadSource": "Email Inquiry",
                "Status": "Open - Not Contacted",
                "Description": "자동 이메일 워크플로우를 통해 생성된 Lead"
            }
            
            # Lead 생성 API 호출
            lead_url = f"{self.instance_url}/services/data/v60.0/sobjects/Lead/"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"Lead 생성 요청: {lead_data['FirstName']} {lead_data['LastName']} ({lead_data['Company']})")
            
            response = requests.post(lead_url, headers=headers, json=lead_data)
            
            if response.status_code == 201:
                result = response.json()
                lead_id = result['id']
                
                self.logger.info(f"✅ Lead 생성 성공!")
                self.logger.info(f"   Lead ID: {lead_id}")
                self.logger.info(f"   Lead URL: {self.instance_url}/lightning/r/Lead/{lead_id}/view")
                return True
            else:
                self.logger.error(f"Lead 생성 실패: {response.status_code}")
                self.logger.error(f"   응답: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Lead 생성 중 오류: {e}")
            return False
    
    def verify_lead(self, lead_id: str) -> Optional[Dict]:
        """생성된 Lead 정보 확인"""
        if not self.access_token or not self.instance_url:
            return None
        
        try:
            lead_url = f"{self.instance_url}/services/data/v60.0/sobjects/Lead/{lead_id}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(lead_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Lead 정보 확인 실패: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lead 확인 중 오류: {e}")
            return None