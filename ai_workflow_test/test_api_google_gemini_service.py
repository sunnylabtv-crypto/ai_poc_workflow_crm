import json
import requests
from typing import Optional, Dict, Any

class GeminiService:
    """Gemini API 서비스 클래스"""
    
    def __init__(self, config):
        """
        Gemini 서비스 초기화
        
        Args:
            config: Config 객체
        """
        self.config = config
    
    def test_connection(self) -> bool:
        """Gemini API 연결 테스트"""
        print("=== Gemini API 연결 테스트 ===")
        
        try:
            url = f"{self.config.gemini_base_url}/models/{self.config.gemini_model}:generateContent"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{
                        "text": "안녕하세요! 간단한 인사말로 답변해주세요."
                    }]
                }]
            }
            
            response = requests.post(
                f"{url}?key={self.config.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ Gemini API 연결 성공!")
                    print(f"   응답: {answer.strip()}")
                    return True
                else:
                    print(f"❌ 예상과 다른 응답 형식: {result}")
                    return False
            else:
                print(f"❌ API 연결 실패 ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Gemini API 테스트 실패: {e}")
            return False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> Optional[str]:
        """
        텍스트 생성
        
        Args:
            prompt: 입력 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            
        Returns:
            Optional[str]: 생성된 텍스트
        """
        try:
            url = f"{self.config.gemini_base_url}/models/{self.config.gemini_model}:generateContent"
            
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
                f"{url}?key={self.config.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    print("응답에서 텍스트를 찾을 수 없습니다.")
                    return None
            else:
                print(f"❌ 텍스트 생성 실패 ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 텍스트 생성 중 오류: {e}")
            return None
    
    def generate_email_content(self, topic: str) -> Optional[Dict[str, str]]:
        """
        이메일 내용 생성
        
        Args:
            topic: 이메일 주제
            
        Returns:
            Optional[Dict[str, str]]: {"subject": "제목", "body": "본문"}
        """
        prompt = f"""
다음 주제로 전문적이고 정중한 이메일을 작성해주세요:

주제: {topic}

이메일 구성:
- 적절한 제목
- 인사말
- 본문 (200자 내외)
- 맺음말

JSON 형식으로 응답해주세요:
{{
    "subject": "이메일 제목",
    "body": "이메일 본문"
}}
"""
        
        try:
            response_text = self.generate_text(prompt, temperature=0.7)
            if not response_text:
                return None
            
            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                content = response_text
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                email_data = json.loads(content)
                return email_data
                
            except json.JSONDecodeError:
                print(f"JSON 파싱 실패. 원본 응답 사용: {response_text}")
                return {
                    "subject": f"{topic} 관련 메시지",
                    "body": response_text
                }
                
        except Exception as e:
            print(f"이메일 생성 중 오류: {e}")
            return None
    
    def list_models(self) -> Optional[Dict[str, Any]]:
        """사용 가능한 모델 목록 조회"""
        try:
            url = f"{self.config.gemini_base_url}/models"
            
            response = requests.get(
                f"{url}?key={self.config.gemini_api_key}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 모델 목록 조회 실패 ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 모델 목록 조회 중 오류: {e}")
            return None