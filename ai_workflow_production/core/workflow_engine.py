# core/workflow_engine.py - 워크플로우 엔진 (수정 완료)

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

# config.py의 함수를 직접 사용합니다.
from ai_workflow_production import config

# 각 v2 서비스들을 가져옵니다.
from ai_workflow_production.services.service_manager import ServiceManager
from ai_workflow_production.services.gmail_service_v2 import GmailServiceV2
from ai_workflow_production.services.gemini_service_v2 import GeminiServiceV2
from ai_workflow_production.services.salesforce_service_v2 import SalesforceServiceV2

class WorkflowEngine:
    """워크플로우 엔진 - Level 1, 2 처리"""
    
    def __init__(self, environment='development'):
        self.logger = logging.getLogger(__name__)
        self.environment = environment
        # config.py의 함수를 사용해 설정을 로드합니다.
        self.config = config.load_environment_config(environment)
        
        self.service_manager = ServiceManager()
        self.processed_emails = set()
        
        # 서비스 설정 메서드를 호출합니다.
        self._setup_services()
        
        self.logger.info(f"워크플로우 엔진 초기화 - 환경: {environment}")
    
    def _setup_services(self):
        """서비스 등록"""
        self.logger.info("서비스 등록 중...")
        
        try:
            # ========================================================== #
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 핵심 수정 사항 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ #
            # 각 서비스 생성자에 self.config 객체를 전달합니다.
            # 이제 각 서비스는 필요한 모든 설정 정보를 갖고 시작합니다.
            # ========================================================== #
            self.service_manager.register_service("gmail", GmailServiceV2(self.config))
            self.service_manager.register_service("gemini", GeminiServiceV2(self.config))
            self.service_manager.register_service("salesforce", SalesforceServiceV2(self.config))
            
        except Exception as e:
            self.logger.error(f"서비스 등록 실패: {e}", exc_info=True)
            raise  # 등록 실패 시 엔진을 멈추도록 예외를 다시 발생시킵니다.

    def initialize(self) -> bool:
        """워크플로우 엔진 초기화"""
        self.logger.info("=" * 60)
        self.logger.info("워크플로우 엔진 초기화")
        self.logger.info("=" * 60)
        
        result = self.service_manager.initialize_all()
        
        if result:
            self.logger.info("✅ 워크플로우 엔진 초기화 완료")
        else:
            self.logger.error("❌ 워크플로우 엔진 초기화 실패")
        
        return result
    
    def process_new_emails(self, lookback_minutes: int = None, max_emails: int = None) -> List[Dict]:
        """새 이메일 처리"""
        self.logger.info("\n📧 새 이메일 처리 시작")
        
        if lookback_minutes is None:
            lookback_minutes = self.config['WORKFLOW_CONFIG']['EMAIL_LOOKBACK_MINUTES']
        if max_emails is None:
            max_emails = self.config['WORKFLOW_CONFIG']['MAX_EMAILS_PER_CHECK']
        
        try:
            gmail_service = self.service_manager.get_service("gmail")
            if not gmail_service:
                self.logger.error("Gmail 서비스를 사용할 수 없습니다")
                return []
            
            new_emails = gmail_service.get_recent_emails(lookback_minutes, max_emails)
            
            if not new_emails:
                self.logger.info("처리할 새 이메일 없음")
                return []
            
            unique_emails = [email for email in new_emails if email.get('id') not in self.processed_emails]
            
            if not unique_emails:
                self.logger.info("모든 이메일이 이미 처리됨")
                return []
            
            self.logger.info(f"🎉 {len(unique_emails)}개 새 이메일 발견")
            
            results = []
            for i, email in enumerate(unique_emails, 1):
                self.logger.info(f"\n{'─' * 60}")
                self.logger.info(f"[{i}/{len(unique_emails)}] 이메일 처리 중")
                
                result = self._process_single_email(email)
                if result:
                    results.append(result)
                    self.processed_emails.add(email.get('id'))
            
            self.logger.info(f"\n✅ 이메일 처리 완료: {len(results)}개")
            return results
            
        except Exception as e:
            self.logger.error(f"이메일 처리 중 오류: {e}", exc_info=True)
            return []

    def _process_single_email(self, email: Dict) -> Optional[Dict]:
        """개별 이메일 처리"""
        sender = email.get('sender', '')
        subject = email.get('subject', '')
        content = email.get('content', '')
        
        self.logger.info(f"📧 발신자: {sender}")
        self.logger.info(f"📋 제목: {subject}")
        
        try:
            # Level 1: Gemini를 이용한 정보 추출 및 답장 생성/발송
            level1_result = self._execute_level1_workflow(sender, subject, content, email.get('id'))
            customer_info = level1_result.get('customer_info')
            
            # Level 2: 정보가 완전할 경우 Salesforce Lead 생성
            if customer_info and customer_info.get('has_all_info'):
                self._execute_level2_workflow(customer_info)
            else:
                self.logger.info("🔷 Level 2: 정보 부족으로 Lead 생성 건너뜀")

            self.logger.info("✅ 이메일 처리 완료")
            return level1_result

        except Exception as e:
            self.logger.error(f"개별 이메일 처리 실패: {e}", exc_info=True)
            return None

    def _execute_level1_workflow(self, sender: str, subject: str, content: str, email_id: str) -> Dict:
        """Level 1: 자동 답장 (고객 정보 추출 포함)"""
        self.logger.info("\n🔷 Level 1: 답장 처리 시작")
        gemini_service = self.service_manager.get_service("gemini")
        gmail_service = self.service_manager.get_service("gmail")
        
        # 1. 고객 정보 추출
        customer_info = gemini_service.extract_customer_info(content, sender)
        
        # 2. 답변 생성
        reply = gemini_service.generate_reply(customer_info, subject)
        
        # 3. 답장 발송
        reply_sent = gmail_service.send_reply(
            to_email=customer_info['email'],
            subject=reply['subject'],
            content=reply['body'],
            original_email_id=email_id
        )
        
        if reply_sent:
            self.logger.info("✅ Level 1 완료: 답장 발송 성공")
        else:
            self.logger.error("❌ Level 1 실패: 답장 발송 실패")
            
        return {'customer_info': customer_info, 'reply_sent': reply_sent}

    def _execute_level2_workflow(self, customer_info: Dict) -> bool:
        """Level 2: Lead 생성 (정보가 완전한 경우만)"""
        self.logger.info("\n🔷 Level 2: Lead 생성 시작")
        salesforce_service = self.service_manager.get_service("salesforce")
        
        lead_created = salesforce_service.create_lead(customer_info)
        
        if lead_created:
            self.logger.info("✅ Level 2 완료: Lead 생성 성공")
        else:
            self.logger.error("❌ Level 2 실패: Lead 생성 실패")
            
        return lead_created

    # run_single, run_monitor, health_check 메서드는 기존과 동일하게 유지합니다.
    # (코드가 길어 생략)
    def run_monitor(self):
        """모니터링 모드 (지속 실행)"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("모니터링 모드 시작")
        self.logger.info("=" * 60)
        
        if not self.initialize():
            self.logger.error("초기화 실패로 모니터링을 시작할 수 없습니다.")
            return
        
        interval = self.config['WORKFLOW_CONFIG']['EMAIL_CHECK_INTERVAL']
        
        check_count = 0
        try:
            while True:
                check_count += 1
                self.logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 체크 #{check_count}")
                self.process_new_emails()
                self.logger.info(f"⏰ 다음 체크: {interval}초 후...\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("\n\n⏹️  모니터링 중단")