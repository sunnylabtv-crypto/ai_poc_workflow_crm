import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional

class GmailService:
    """Gmail API 서비스 클래스"""
    
    def __init__(self, config):
        """
        Gmail 서비스 초기화
        
        Args:
            config: Config 객체
        """
        self.config = config
        self.service = None
        self.user_email = None
    
    def authenticate(self) -> bool:
        """Gmail API 인증"""
        print("=== Gmail API 인증 ===")
        
        creds = None
        
        # 기존 토큰 파일 로드
        if os.path.exists(self.config.gmail_token_path):
            creds = Credentials.from_authorized_user_file(
                self.config.gmail_token_path, 
                self.config.gmail_scopes
            )
        
        # 토큰이 없거나 유효하지 않으면 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("토큰 새로고침 중...")
                    creds.refresh(Request())
                    print("✅ 토큰 새로고침 완료")
                except Exception as e:
                    print(f"토큰 새로고침 실패: {e}")
                    creds = None
            
            if not creds:
                print("브라우저에서 Google 계정 인증을 진행합니다...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.gmail_credentials_path, 
                    self.config.gmail_scopes
                )
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            # os.makedirs(os.path.dirname(self.config.gmail_token_path), exist_ok=True)
            token_dir = os.path.dirname(self.config.gmail_token_path)
            if token_dir:  # 디렉토리가 있을 때만 생성
                os.makedirs(token_dir, exist_ok=True)
            
            with open(self.config.gmail_token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']
            print(f"✅ Gmail API 인증 성공! 계정: {self.user_email}")
            return True
        except Exception as e:
            print(f"❌ Gmail API 인증 실패: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        이메일 전송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            body: 본문
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.service:
            print("❌ Gmail 서비스가 초기화되지 않았습니다.")
            return False
        
        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = self.user_email
            message['subject'] = subject
            
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"✅ 이메일 전송 성공! 메시지 ID: {result['id']}")
            return True
            
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        if not self.authenticate():
            return False
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            print("✅ Gmail API 연결 테스트 성공!")
            print(f"   이메일: {profile['emailAddress']}")
            print(f"   총 메시지 수: {profile.get('messagesTotal', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ Gmail API 연결 테스트 실패: {e}")
            return False
        

    def get_recent_emails(self, minutes_ago: int = 10, max_results: int = 10):
        """
        최근 이메일 조회
        
        Args:
            minutes_ago: 몇 분 전 이메일까지 조회할지
            max_results: 최대 조회 개수
            
        Returns:
            list: 이메일 리스트
        """
        if not self.service:
            print("❌ Gmail 서비스가 초기화되지 않았습니다.")
            return []
        
        try:
            from datetime import datetime, timedelta
            
            # 시간 계산
            after_time = datetime.now() - timedelta(minutes=minutes_ago)
            query = f'after:{int(after_time.timestamp())}'
            
            # 이메일 검색
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            print(f"📧 {len(messages)}개 이메일 조회 중...")
            
            for msg in messages:
                try:
                    # 이메일 상세 정보 가져오기
                    email_data = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # 헤더에서 정보 추출
                    headers = email_data['payload']['headers']
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # 본문 추출
                    content = ''
                    if 'parts' in email_data['payload']:
                        for part in email_data['payload']['parts']:
                            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                                import base64
                                content = base64.urlsafe_b64decode(
                                    part['body']['data']
                                ).decode('utf-8', errors='ignore')
                                break
                    elif 'body' in email_data['payload'] and 'data' in email_data['payload']['body']:
                        import base64
                        content = base64.urlsafe_b64decode(
                            email_data['payload']['body']['data']
                        ).decode('utf-8', errors='ignore')
                    
                    emails.append({
                        'id': msg['id'],
                        'sender': sender,
                        'subject': subject,
                        'date': date,
                        'content': content
                    })
                    
                except Exception as e:
                    print(f"⚠️ 이메일 처리 중 오류: {e}")
                    continue
            
            print(f"✅ {len(emails)}개 이메일 조회 완료")
            return emails
            
        except Exception as e:
            print(f"❌ 이메일 조회 실패: {e}")
            return []

    def send_reply(self, to_email: str, subject: str, content: str, original_email_id: str = None):
        """답장 발송 (send_email 메서드 재사용)"""
        return self.send_email(to_email, subject, content)