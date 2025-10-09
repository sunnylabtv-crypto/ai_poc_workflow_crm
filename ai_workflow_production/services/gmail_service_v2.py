# services/gmail_service_v2.py (최종 수정 완료)

import os
import base64
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import List, Dict

from .base_service import BaseService

class GmailServiceV2(BaseService):
    """Gmail API 서비스 (독립 실행 버전)"""

    def __init__(self, config):
        super().__init__("Gmail")
        
        gmail_config = config['GMAIL_CONFIG']
        self.scopes = gmail_config['SCOPES']
        self.token_path = gmail_config['TOKEN_FILE']
        self.credentials_path = gmail_config['CREDENTIALS_FILE']
        
        self.service = None
        self.user_email = None

    def authenticate(self) -> bool:
        """Gmail API 인증 및 서비스 객체 생성"""
        self.logger.info("Gmail 서비스 인증 시작...")
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"토큰 새로고침 실패: {e}. 새로 인증합니다.")
                    creds = None # 새로 인증하도록 creds를 초기화
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"새 인증 흐름 실패: {e}", exc_info=True)
                    return False

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']
            self.logger.info(f"✅ Gmail 인증 성공! 계정: {self.user_email}")
            return True
        except Exception as e:
            self.logger.error(f"Gmail 서비스 빌드 실패: {e}", exc_info=True)
            return False

    def get_recent_emails(self, minutes_ago: int = 10, max_results: int = 10) -> List[Dict]:
        """최근 이메일 조회 (자신이 보낸 이메일 제외)"""
        if not self.service:
            self.logger.error("❌ Gmail 서비스가 초기화되지 않았습니다.")
            return []

        def _get_emails():
            after_time = datetime.now() - timedelta(minutes=minutes_ago)
            
            # ✅ 핵심 수정: 자신이 보낸 이메일 제외 + 받은편지함만
            query = f'after:{int(after_time.timestamp())} -from:me in:inbox'
            
            self.logger.info(f"이메일 검색 쿼리: {query}")
            
            results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                try:
                    email_data = self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                    
                    headers = email_data['payload']['headers']
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                    
                    # ✅ 추가 안전장치: 발신자가 자신인지 다시 한 번 체크
                    if self.user_email and self.user_email.lower() in sender.lower():
                        self.logger.info(f"자신이 보낸 이메일 건너뜀: {sender}")
                        continue
                    
                    content = ""
                    if 'parts' in email_data['payload']:
                        for part in email_data['payload']['parts']:
                            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                                content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                                break
                    elif 'body' in email_data['payload'] and 'data' in email_data['payload']['body']:
                        content = base64.urlsafe_b64decode(email_data['payload']['body']['data']).decode('utf-8', errors='ignore')

                    emails.append({
                        'id': msg['id'], 'sender': sender, 'subject': subject, 'content': content.strip()
                    })
                except Exception as e:
                    self.logger.warning(f"개별 이메일 파싱 실패: {e}")
                    continue
            
            if emails:
                self.logger.info(f"✅ {len(emails)}개의 새 이메일 발견 (자신이 보낸 이메일 제외)")
            
            return emails

        return self.execute_with_retry("최근 이메일 조회", _get_emails) or []

    def send_reply(self, to_email: str, subject: str, content: str, original_email_id: str = None) -> bool:
        """답장 발송"""
        if not self.service:
            self.logger.error("❌ Gmail 서비스가 초기화되지 않았습니다.")
            return False
            
        def _send():
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = self.user_email
            message['subject'] = subject
            message.attach(MIMEText(content, 'plain', 'utf-8'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            return True

        return self.execute_with_retry(f"답장 발송 ({to_email})", _send) or False