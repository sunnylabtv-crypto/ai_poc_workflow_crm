# services/gemini_service_v2.py

from services.base_service import BaseService
import os
import json
import re
import requests
from typing import Dict, Optional

class GeminiServiceV2(BaseService):
    """Gemini AI 서비스"""
    
    def __init__(self, config_obj):
        super().__init__("Gemini")
        
        # Config에서 설정 가져오기
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = 'https://generativelanguage.googleapis.com/v1'
        self.model = 'gemini-2.0-flash-lite'
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다")
        
        self.logger.info(f"Gemini 서비스 초기화 - 모델: {self.model}")
        
      # 2. 바로 이 위치에 authenticate 메서드를 추가합니다.
    def authenticate(self) -> bool:
        """Gemini API 연결을 테스트하여 인증을 수행합니다."""
        self.logger.info("Gemini 서비스 인증 시도...")
        return self.test_connection()
    
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> Optional[str]:
        """
        텍스트 생성 (검증된 코드 사용)
        
        Args:
            prompt: 입력 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            
        Returns:
            Optional[str]: 생성된 텍스트
        """
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.8,
                    "topK": 10
                }
            }
            
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    self.logger.info("텍스트 생성 성공")
                    return text
                else:
                    self.logger.error("응답에서 텍스트를 찾을 수 없습니다.")
                    return None
            else:
                self.logger.error(f"텍스트 생성 실패 ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"텍스트 생성 중 오류: {e}")
            return None
    
    def extract_customer_info(self, email_content: str, sender_email: str) -> Dict:
        """
        이메일에서 고객 정보 추출
        
        Returns:
            {
                'has_all_info': bool,
                'name': str,
                'company': str,
                'title': str,
                'phone': str,
                'email': str,
                'missing_fields': list
            }
        """
        try:
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 이 프롬프트를 교체하세요 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            prompt = f"""
Analyze the following email content to extract customer information.
The content may include replies or forwarded messages. Ignore quoted text, previous email threads, and signatures. Focus only on the information provided in the most recent message part.

Email Content:
---
{email_content}
---

From the text above, extract the following fields and respond ONLY in a valid JSON format.
If a piece of information is not found, the value should be null.
The "email" field should default to the sender's email if not present in the body.

Sender's Email: {sender_email}

Required fields:
1. name: Full name of the person (e.g., "성춘향")
2. company: Company name (e.g., "춘향서비스")
3. title: Job title (e.g., "과장")
4. phone: Contact phone number (e.g., "010-2333-3333")
5. email: Contact email address

JSON response format:
{{
    "name": "value or null",
    "company": "value or null",
    "title": "value or null",
    "phone": "value or null",
    "email": "value or null"
}}
"""
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

            # ... (이하 메서드의 나머지 코드는 그대로) ...
            
            response_text = self.generate_text(prompt, temperature=0.3)
            
            if not response_text:
                raise Exception("Gemini 응답 없음")
            
            # JSON 파싱
            content = response_text
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # JSON에서 중괄호 부분만 추출
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group())
            else:
                info = json.loads(content)
            
            # 발신자 이메일 기본값 설정
            if not info.get('email') or info.get('email') == 'null':
                info['email'] = sender_email
            
            # 누락된 필드 확인
            required_fields = ['name', 'company', 'title', 'phone', 'email']
            missing_fields = []
            
            for field in required_fields:
                value = info.get(field)
                if not value or value == 'null' or value == '':
                    missing_fields.append(field)
            
            result = {
                'has_all_info': len(missing_fields) == 0,
                'name': info.get('name') if info.get('name') != 'null' else None,
                'company': info.get('company') if info.get('company') != 'null' else None,
                'title': info.get('title') if info.get('title') != 'null' else None,
                'phone': info.get('phone') if info.get('phone') != 'null' else None,
                'email': info.get('email', sender_email),
                'missing_fields': missing_fields
            }
            
            self.logger.info(f"고객 정보 추출 완료: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"고객 정보 추출 실패: {e}")
            return {
                'has_all_info': False,
                'name': None,
                'company': None,
                'title': None,
                'phone': None,
                'email': sender_email,
                'missing_fields': ['name', 'company', 'title', 'phone']
            }
    
    def generate_reply(self, customer_info: Dict, original_subject: str) -> Dict:
        """
        고객 정보를 바탕으로 답변 생성
        
        Returns:
            {
                'subject': str,
                'body': str
            }
        """
        try:
            if customer_info['has_all_info']:
                # 모든 정보가 있는 경우
                prompt = f"""
고객이 다음 정보와 함께 문의했습니다:
- 이름: {customer_info['name']}
- 회사: {customer_info['company']}
- 직급: {customer_info['title']}
- 전화번호: {customer_info['phone']}
- 이메일: {customer_info['email']}

원본 제목: {original_subject}

다음 내용으로 정중한 답변 이메일을 작성해주세요:
1. 문의에 감사 인사
2. 고객님의 정보를 확인했다고 말하기
3. 담당 영업팀에 연결하여 신속히 연락드리겠다고 안내
4. 빠른 시일 내 연락드릴 것을 약속
5. "감사합니다" 마무리

전문적이고 친절한 톤으로 한국어로 작성하세요.
"""
            else:
                # 정보가 부족한 경우
                missing_kr = {
                    'name': '성함',
                    'company': '소속/회사명',
                    'title': '직급',
                    'phone': '연락처',
                    'email': '이메일'
                }
                missing_list = [missing_kr.get(f, f) for f in customer_info['missing_fields']]
                
                prompt = f"""
고객이 문의 이메일을 보냈지만 다음 정보가 누락되었습니다:
{', '.join(missing_list)}

원본 제목: {original_subject}

다음 내용으로 정중한 답변 이메일을 작성해주세요:
1. 문의에 감사 인사
2. 정확한 상담을 위해 추가 정보가 필요하다고 설명
3. 누락된 정보 목록을 정중히 요청:
   - {chr(10).join(['   - ' + m for m in missing_list])}
4. 정보 제공 시 신속히 답변 드리겠다고 안내
5. "감사합니다" 마무리

전문적이고 친절한 톤으로 한국어로 작성하세요.
"""
            
            body = self.generate_text(prompt, temperature=0.7)
            
            if not body:
                raise Exception("답변 생성 실패")
            
            # 제목 생성
            if customer_info['has_all_info']:
                subject = f"Re: {original_subject} - 담당자 배정 완료"
            else:
                subject = f"Re: {original_subject} - 추가 정보 요청"
            
            return {
                'subject': subject,
                'body': body
            }
            
        except Exception as e:
            self.logger.error(f"답변 생성 실패: {e}")
            return {
                'subject': f"Re: {original_subject}",
                'body': "문의 주셔서 감사합니다. 빠른 시일 내에 답변 드리겠습니다."
            }
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{
                        "text": "안녕하세요! 간단한 인사말로 답변해주세요."
                    }]
                }]
            }
            
            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    self.logger.info("✅ Gemini API 연결 테스트 성공")
                    return True
            
            self.logger.error(f"Gemini API 연결 테스트 실패: {response.status_code}")
            return False
                
        except Exception as e:
            self.logger.error(f"Gemini API 테스트 실패: {e}")
            return False