# 메인 Flask 파일 (gpt_3gmail_autosending.py) 상단을 다음과 같이 수정하세요:

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os  # 이 줄이 누락되었을 수 있음
import base64
import json
from datetime import datetime, timedelta
from openai import OpenAI  # 새로운 OpenAI import
from dotenv import load_dotenv  # 환경변수 로드용
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import threading
import time
from werkzeug.security import generate_password_hash, check_password_hash

# 환경 변수 로드
load_dotenv()

# 현재 파일의 디렉토리를 기준으로 templates 폴더 경로 설정
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)  # 이 줄이 있어야 함
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# OpenAI 클라이언트 전역 초기화
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 설정
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

class EmailAssistant:
    def __init__(self):
        self.init_database()
        # 전역 OpenAI 클라이언트 사용
        self.openai_client = openai_client
    
    def init_database(self):
        """SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect('email_assistant.db')
        cursor = conn.cursor()
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                credentials TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 이메일 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                gmail_id TEXT,
                sender TEXT,
                subject TEXT,
                content TEXT,
                received_at TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 초안 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                email_id INTEGER,
                original_subject TEXT,
                draft_subject TEXT,
                draft_content TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def generate_reply_draft(self, email_content, sender, subject):
        """ChatGPT로 답변 초안 생성"""
        try:
            print(f"AI 답변 생성 시작...")
            print(f"보낸이: {sender}")
            print(f"제목: {subject}")
            
            prompt = f'''다음 이메일에 대한 전문적이고 정중한 답변을 작성해주세요:

보낸 사람: {sender}
제목: {subject}
내용:
{email_content}

답변 요구사항:
1. 정중하고 전문적인 톤
2. 핵심 내용에 대한 적절한 응답
3. 한국어로 작성
4. 200-400자 길이

답변 형식:
제목: [답변 제목]
내용: [답변 내용]
'''
            
            print("OpenAI API 호출 중...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문적이고 정중한 이메일 답변을 작성하는 도우미입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            reply_text = response.choices[0].message.content.strip()
            print(f"AI 답변 생성 완료")
            
            # 제목과 내용 분리
            lines = reply_text.split('\n')
            draft_subject = lines[0].replace('제목:', '').strip() if lines else f"Re: {subject}"
            draft_content = '\n'.join(lines[1:]).replace('내용:', '').strip() if len(lines) > 1 else reply_text
            
            return draft_subject, draft_content
            
        except Exception as e:
            print(f"AI 답변 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return f"Re: {subject}", "죄송합니다. 답변을 검토 후 회신드리겠습니다."

    # ... 나머지 메서드들 (get_gmail_service, save_credentials, fetch_new_emails, extract_email_content, send_email)

# 전역 EmailAssistant 인스턴스
assistant = EmailAssistant()

# ... 모든 Flask 라우트들 (@app.route 들)

if __name__ == '__main__':
    print("=" * 50)
    print("환경 설정 확인 중...")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"OpenAI API 키: 설정됨 ({api_key[:20]}...)")
    else:
        print("OpenAI API 키: 설정되지 않음")
    
    # credentials.json 확인
    if os.path.exists('credentials.json'):
        print("credentials.json: 존재함")
    else:
        print("credentials.json: 없음")
    
    print("=" * 50)
    print("Flask 앱 시작...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)