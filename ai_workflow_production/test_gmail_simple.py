import config

# Config 객체 클래스
class ConfigObj:
    def __init__(self):
        env_config = config.load_environment_config('development')
        gmail_cfg = env_config['GMAIL_CONFIG']
        
        self.gmail_token_path = gmail_cfg['TOKEN_FILE']
        self.gmail_credentials_path = gmail_cfg['CREDENTIALS_FILE']
        self.gmail_scopes = gmail_cfg['SCOPES']

# Gmail 서비스 테스트
def test_gmail():
    config_obj = ConfigObj()
    
    from services.gmail_service_v2 import GmailServiceV2
    gmail = GmailServiceV2(config_obj)
    
    # 인증
    print("🔐 Gmail 인증 중...")
    result = gmail.authenticate()
    print(f"인증 결과: {result}")
    
    if result:
        # 이메일 조회
        print("\n📧 최근 이메일 조회 중...")
        emails = gmail.get_recent_emails(minutes_ago=60, max_results=10)
        print(f"조회된 이메일: {len(emails)}개\n")
        
        for i, email in enumerate(emails, 1):
            print(f"{i}. 발신자: {email['sender']}")
            print(f"   제목: {email['subject']}\n")
    else:
        print("❌ 인증 실패")

if __name__ == "__main__":
    test_gmail()