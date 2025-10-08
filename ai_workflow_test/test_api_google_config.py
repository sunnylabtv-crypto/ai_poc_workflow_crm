import os
from dotenv import load_dotenv

class Config:
    """환경 설정 관리 클래스"""
    
    def __init__(self):
        # .env 파일 로드
        load_dotenv()
        
        # Gemini API 설정
        # Gemini API 설정
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1"
        self.gemini_model = "gemini-2.0-flash-lite"

        # Gmail API 설정
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.gmail_credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', os.path.join(script_dir, 'credentials_new.json'))
        self.gmail_token_path = os.getenv('GMAIL_TOKEN_PATH', os.path.join(script_dir, 'token_new.json'))
        self.gmail_scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
    
    def validate_environment(self):
        """환경 설정 유효성 검사"""
        issues = []
        
        # .env 파일 확인
        if not os.path.exists('.env'):
            issues.append("❌ .env 파일이 없습니다.")
        
        # Gemini API 키 확인
        if not self.gemini_api_key:
            issues.append("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        
        # Gmail credentials 파일 확인
        if not os.path.exists(self.gmail_credentials_path):
            issues.append(f"❌ Gmail credentials 파일이 없습니다: {self.gmail_credentials_path}")
        
        # 필수 라이브러리 확인
        try:
            import google.auth
        except ImportError:
            issues.append("❌ Google API 라이브러리가 설치되지 않았습니다.")
        
        try:
            import dotenv
        except ImportError:
            issues.append("❌ python-dotenv 라이브러리가 설치되지 않았습니다.")
        
        return issues
    
    def print_status(self):
        """설정 상태 출력"""
        print("=== 환경 설정 상태 ===")
        print(f"Gmail credentials: {self.gmail_credentials_path}")
        print(f"Gmail token: {self.gmail_token_path}")
        print(f"Gemini API key: {'설정됨' if self.gemini_api_key else '미설정'}")
        
        issues = self.validate_environment()
        if issues:
            print("\n문제점:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ 모든 환경 설정이 완료되었습니다!")
            return True