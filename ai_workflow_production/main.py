# main.py - AI Workflow Production 메인 실행 파일

import argparse
import time
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

import config
from services.gmail_service_v2 import GmailServiceV2
from services.gemini_service_v2 import GeminiServiceV2
from services.salesforce_service_v2 import SalesforceServiceV2
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/workflow.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WorkflowEngine:
    """워크플로우 엔진"""
    
    def __init__(self, environment='development'):
        """초기화"""
        self.environment = environment
        self.config = config.load_environment_config(environment)
        
        # Config 객체 생성 (레거시 서비스용)
        self.config_obj = self._create_config_object()
        
        # 서비스 초기화
        self.gmail = None
        self.gemini = None
        self.salesforce = None
        
        logger.info(f"워크플로우 엔진 초기화 - 환경: {environment}")
    
    def _create_config_object(self):
        """레거시 서비스를 위한 Config 객체 생성"""
        class ConfigObj:
            def __init__(self, config_dict):
                gmail_cfg = config_dict['GMAIL_CONFIG']
                self.gmail_token_path = gmail_cfg['TOKEN_FILE']
                self.gmail_credentials_path = gmail_cfg['CREDENTIALS_FILE']
                self.gmail_scopes = gmail_cfg['SCOPES']
                
                gemini_cfg = config_dict['GEMINI_CONFIG']
                self.gemini_api_key = gemini_cfg.get('API_KEY_ENV', '')
                
                sf_cfg = config_dict['SALESFORCE_CONFIG']
                self.sf_username = sf_cfg.get('USERNAME_ENV', '')
                self.sf_password = sf_cfg.get('PASSWORD_ENV', '')
        
        return ConfigObj(self.config)
    
    def initialize_services(self):
        """모든 서비스 초기화"""
        logger.info("서비스 초기화 시작...")
        
        try:
            # Gmail 서비스
            logger.info("Gmail 서비스 초기화 중...")
            self.gmail = GmailServiceV2(self.config_obj)
            if not self.gmail.authenticate():
                logger.error("Gmail 인증 실패")
                return False
            logger.info("✅ Gmail 서비스 초기화 완료")
            
            # Gemini 서비스 (선택적)
            try:
                logger.info("Gemini 서비스 초기화 중...")
                self.gemini = GeminiServiceV2()
                logger.info("✅ Gemini 서비스 초기화 완료")
            except Exception as e:
                logger.warning(f"Gemini 서비스 초기화 실패 (계속 진행): {e}")
            
            # Salesforce 서비스 (선택적)
            try:
                logger.info("Salesforce 서비스 초기화 중...")
                self.salesforce = SalesforceServiceV2()
                logger.info("✅ Salesforce 서비스 초기화 완료")
            except Exception as e:
                logger.warning(f"Salesforce 서비스 초기화 실패 (계속 진행): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"서비스 초기화 중 오류: {e}")
            return False
    
    def process_email(self, email):
        """개별 이메일 처리"""
        try:
            sender = email['sender']
            subject = email['subject']
            content = email['content']
            
            logger.info(f"이메일 처리 중 - 발신자: {sender}, 제목: {subject}")
            
            # 1. Gemini로 이메일 분석 (가능한 경우)
            if self.gemini:
                try:
                    analysis = self.gemini.analyze_email(content)
                    logger.info(f"이메일 분석 완료: {analysis}")
                except Exception as e:
                    logger.warning(f"이메일 분석 실패: {e}")
                    analysis = None
            else:
                analysis = None
            
            # 2. Salesforce에 리드 생성 (가능한 경우)
            if self.salesforce and analysis:
                try:
                    lead_data = {
                        'email': sender,
                        'subject': subject,
                        'description': content[:500]
                    }
                    self.salesforce.create_lead(lead_data)
                    logger.info("Salesforce 리드 생성 완료")
                except Exception as e:
                    logger.warning(f"Salesforce 리드 생성 실패: {e}")
            
            # 3. 답장 생성 및 발송 (필요한 경우)
            # TODO: 비즈니스 로직에 따라 자동 답장 구현
            
            logger.info(f"✅ 이메일 처리 완료 - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 처리 중 오류: {e}")
            return False
    
    def run_single(self):
        """단일 실행 모드"""
        logger.info("=== 단일 실행 모드 시작 ===")
        
        if not self.initialize_services():
            logger.error("서비스 초기화 실패")
            return
        
        # 최근 이메일 조회
        lookback = self.config['WORKFLOW_CONFIG']['EMAIL_LOOKBACK_MINUTES']
        max_emails = self.config['WORKFLOW_CONFIG']['MAX_EMAILS_PER_CHECK']
        
        logger.info(f"최근 {lookback}분간 이메일 조회 중...")
        emails = self.gmail.get_recent_emails(
            minutes_ago=lookback,
            max_results=max_emails
        )
        
        if not emails:
            logger.info("처리할 이메일이 없습니다.")
            return
        
        logger.info(f"{len(emails)}개 이메일 발견")
        
        # 이메일 처리
        for i, email in enumerate(emails, 1):
            logger.info(f"[{i}/{len(emails)}] 이메일 처리 중...")
            self.process_email(email)
        
        logger.info("=== 단일 실행 완료 ===")
    
    def run_monitor(self):
        """모니터링 모드 (지속 실행)"""
        logger.info("=== 모니터링 모드 시작 ===")
        
        if not self.initialize_services():
            logger.error("서비스 초기화 실패")
            return
        
        check_interval = self.config['WORKFLOW_CONFIG']['EMAIL_CHECK_INTERVAL']
        max_emails = self.config['WORKFLOW_CONFIG']['MAX_EMAILS_PER_CHECK']
        
        logger.info(f"이메일 체크 간격: {check_interval}초")
        logger.info("Ctrl+C를 눌러 중단할 수 있습니다.")
        logger.info("=" * 60)
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"\n[{current_time}] 체크 #{check_count}")
                
                # 이메일 조회
                emails = self.gmail.get_recent_emails(
                    minutes_ago=5,
                    max_results=max_emails
                )
                
                if emails:
                    logger.info(f"🎉 새 이메일 {len(emails)}개 발견!")
                    
                    for i, email in enumerate(emails, 1):
                        logger.info(f"\n📧 이메일 #{i}/{len(emails)}")
                        logger.info(f"  발신자: {email['sender']}")
                        logger.info(f"  제목: {email['subject']}")
                        
                        self.process_email(email)
                else:
                    logger.info("✅ 새 이메일 없음")
                
                # 대기
                logger.info(f"⏰ 다음 체크: {check_interval}초 후...\n")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  모니터링 중단됨")
            logger.info("프로그램을 종료합니다.")
    
    def health_check(self):
        """헬스 체크"""
        logger.info("=== 헬스 체크 시작 ===")
        
        print("\n📊 시스템 상태 확인")
        print("=" * 60)
        
        # Config 검증
        print("\n1️⃣ 설정 파일 검증...")
        if config.validate_config(self.environment):
            print("   ✅ 설정 파일 정상")
        else:
            print("   ❌ 설정 파일 오류")
        
        # 서비스 초기화
        print("\n2️⃣ 서비스 연결 테스트...")
        if self.initialize_services():
            print("   ✅ Gmail: 연결 성공")
            if self.gemini:
                print("   ✅ Gemini: 연결 성공")
            if self.salesforce:
                print("   ✅ Salesforce: 연결 성공")
        else:
            print("   ❌ 서비스 연결 실패")
        
        # 이메일 조회 테스트
        print("\n3️⃣ 이메일 조회 테스트...")
        try:
            emails = self.gmail.get_recent_emails(minutes_ago=60, max_results=5)
            print(f"   ✅ 최근 1시간 이메일: {len(emails)}개")
        except Exception as e:
            print(f"   ❌ 이메일 조회 실패: {e}")
        
        print("\n" + "=" * 60)
        logger.info("=== 헬스 체크 완료 ===")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Workflow Production')
    parser.add_argument(
        '--mode',
        choices=['single', 'monitor', 'health'],
        default='single',
        help='실행 모드: single(단일 실행), monitor(모니터링), health(헬스 체크)'
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production'],
        default='development',
        help='환경 설정: development 또는 production'
    )
    
    args = parser.parse_args()
    
    # 워크플로우 엔진 생성
    engine = WorkflowEngine(environment=args.env)
    
    # 모드에 따라 실행
    if args.mode == 'single':
        engine.run_single()
    elif args.mode == 'monitor':
        engine.run_monitor()
    elif args.mode == 'health':
        engine.health_check()


if __name__ == "__main__":
    main()