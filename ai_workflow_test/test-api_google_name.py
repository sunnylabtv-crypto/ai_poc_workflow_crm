import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailAPISender:
    def __init__(self, credentials_file='./ai-poc-workflow_sfdc/credentials.json', token_file='./ai-poc-workflow_sfdc/token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        self.service = None
        self.user_email = None
        
    def authenticate(self):
        """Google OAuth2 인증"""
        creds = None
        
        # 기존 토큰 파일이 있으면 로드
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # 토큰이 없거나 유효하지 않으면 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("토큰을 새로고침하는 중...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"토큰 새로고침 실패: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ {self.credentials_file} 파일을 찾을 수 없습니다.")
                    print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 credentials.json 파일을 다운로드하세요.")
                    return False
                
                print("브라우저에서 Google 계정 인증을 진행합니다...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # 토큰을 파일에 저장
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            # Gmail 서비스 객체 생성
            self.service = build('gmail', 'v1', credentials=creds)
            
            # 사용자 이메일 주소 가져오기
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']
            
            print(f"✅ Gmail API 인증 성공!")
            print(f"   계정: {self.user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail API 인증 실패: {e}")
            return False
    
    def create_message(self, to_email, subject, body, file_path=None):
        """이메일 메시지 생성"""
        message = MIMEMultipart()
        message['to'] = to_email
        message['from'] = self.user_email
        message['subject'] = subject
        
        # 본문 추가
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 첨부파일이 있다면 추가
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            message.attach(part)
        
        # 메시지를 base64로 인코딩
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def send_email(self, to_email, subject, body, file_path=None):
        """이메일 전송"""
        if not self.service:
            print("❌ 먼저 authenticate() 메서드를 호출하여 인증하세요.")
            return False
        
        try:
            # 메시지 생성
            message = self.create_message(to_email, subject, body, file_path)
            
            # 이메일 전송
            result = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            print(f"✅ 이메일이 성공적으로 전송되었습니다!")
            print(f"   메시지 ID: {result['id']}")
            return True
            
        except HttpError as error:
            print(f"❌ Gmail API 오류: {error}")
            return False
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False
    
    def read_file_content(self, file_path):
        """파일 내용 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return None
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            return None
    
    def send_file_summary(self, summary_file_path, to_email, custom_subject=None):
        """요약 파일을 읽어서 이메일로 전송"""
        # 파일 내용 읽기
        file_content = self.read_file_content(summary_file_path)
        if not file_content:
            return False
        
        # 제목 설정
        if custom_subject:
            subject = custom_subject
        else:
            filename = os.path.basename(summary_file_path)
            subject = f"요약 보고서: {filename}"
        
        # 이메일 본문 구성
        body = f"""안녕하세요,

요약 파일의 내용을 전송드립니다.

파일명: {os.path.basename(summary_file_path)}

--- 내용 ---
{file_content}

감사합니다."""
        
        # 이메일 전송 (파일도 첨부)
        return self.send_email(to_email, subject, body, summary_file_path)
    
    def test_api_connection(self):
        """Gmail API 연결 테스트"""
        if not self.service:
            print("❌ 먼저 인증을 완료하세요.")
            return False
        
        try:
            # 사용자 프로필 정보 가져오기로 연결 테스트
            profile = self.service.users().getProfile(userId='me').execute()
            print("✅ Gmail API 연결 테스트 성공!")
            print(f"   이메일: {profile['emailAddress']}")
            print(f"   총 메시지 수: {profile.get('messagesTotal', 'N/A')}")
            print(f"   총 스레드 수: {profile.get('threadsTotal', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ API 연결 테스트 실패: {e}")
            return False


def check_credentials_file(credentials_path='./ai-poc-workflow_sfdc/credentials.json'):
    """credentials.json 파일 확인"""
    if not os.path.exists(credentials_path):
        print(f"❌ {credentials_path} 파일이 없습니다.")
        print("\n=== Google Cloud Console 설정 방법 ===")
        print("1. https://console.cloud.google.com 접속")
        print("2. 프로젝트 선택 또는 생성")
        print("3. 'API 및 서비스' → '라이브러리'")
        print("4. 'Gmail API' 검색하여 사용 설정")
        print("5. '사용자 인증 정보' → '사용자 인증 정보 만들기' → 'OAuth 클라이언트 ID'")
        print("6. 애플리케이션 유형: '데스크톱 애플리케이션'")
        print("7. JSON 파일 다운로드하여 'credentials.json'으로 저장")
        return False
    
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
            print(f"✅ {credentials_path} 파일 확인됨")
            client_info = creds_data.get('installed', {})
            print(f"   프로젝트 ID: {client_info.get('project_id', 'N/A')}")
            print(f"   클라이언트 ID: {client_info.get('client_id', 'N/A')[:20]}...")
            return True
    except Exception as e:
        print(f"❌ {credentials_path} 파일 읽기 오류: {e}")
        return False


# 사용 예시
def main():
    print("=== Gmail API 이메일 전송 테스트 ===")
    
    # 새 계정의 credentials.json 파일 확인
    credentials_path = './ai-poc-workflow_sfdc/credentials_new.json'  # 새 파일명
    if not check_credentials_file(credentials_path):
        return
    
    # Gmail API 전송기 초기화 (새 계정용)
    sender = GmailAPISender(
        credentials_file=credentials_path,
        token_file='./ai-poc-workflow_sfdc/token_new.json'  # 새 토큰 파일
    )
    
    # Google OAuth2 인증
    print("\n=== Google 계정 인증 ===")
    if not sender.authenticate():
        print("인증에 실패했습니다.")
        return
    
    # API 연결 테스트
    print("\n=== API 연결 테스트 ===")
    if not sender.test_api_connection():
        print("API 연결 테스트에 실패했습니다.")
        return
    
    # 사용자 입력 받기
    print("\n=== 이메일 전송 설정 ===")
    
    # 전송 방법 선택
    print("1. 간단한 텍스트 이메일 전송")
    print("2. 파일 내용을 포함한 이메일 전송")
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    # 수신자 이메일 입력
    recipient = input("수신자 이메일 주소를 입력하세요: ").strip()
    if not recipient:
        print("수신자 이메일이 입력되지 않았습니다.")
        return
    
    if choice == "1":
        # 간단한 이메일 전송
        subject = input("이메일 제목을 입력하세요: ").strip()
        body = input("이메일 내용을 입력하세요: ").strip()
        
        print(f"\n수신자: {recipient}")
        print(f"제목: {subject}")
        print(f"내용: {body}")
        
        confirm = input("\n이메일을 전송하시겠습니까? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            print("\n이메일 전송 중...")
            success = sender.send_email(recipient, subject, body)
            if success:
                print("✅ 이메일 전송 완료!")
            else:
                print("❌ 이메일 전송 실패")
    
    elif choice == "2":
        # 파일 내용 이메일 전송
        summary_file = input("전송할 파일 경로를 입력하세요: ").strip()
        if not summary_file:
            summary_file = "summary_report.txt"
        
        subject = input("이메일 제목을 입력하세요 (엔터: 기본 제목 사용): ").strip()
        if not subject:
            subject = None
        
        print(f"\n파일: {summary_file}")
        print(f"수신자: {recipient}")
        print(f"제목: {subject if subject else '자동 생성'}")
        
        confirm = input("\n이메일을 전송하시겠습니까? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            print("\n이메일 전송 중...")
            success = sender.send_file_summary(summary_file, recipient, subject)
            if success:
                print("✅ 이메일 전송 완료!")
            else:
                print("❌ 이메일 전송 실패")
    
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()