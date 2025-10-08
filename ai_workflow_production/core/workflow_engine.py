# core/workflow_engine.py - 워크플로우 엔진

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import config

from services.service_manager import ServiceManager
from services.gmail_service_v2 import GmailServiceV2
from services.gemini_service_v2 import GeminiServiceV2
from services.salesforce_service_v2 import SalesforceServiceV2

class WorkflowEngine:
    """워크플로우 엔진 - Level 1, 2 처리"""
    
    def __init__(self, environment='development'):
        self.logger = logging.getLogger(__name__)
        self.environment = environment
        self.config = config.load_environment_config(environment)
        
        self.service_manager = ServiceManager()
        self.processed_emails = set()
        
        self._setup_services()
        
        self.logger.info(f"워크플로우 엔진 초기화 - 환경: {environment}")
    
    def _setup_services(self):
        """서비스 등록"""
        self.logger.info("서비스 등록 중...")
        
        try:
            self.service_manager.register_service("gmail", GmailServiceV2())
            self.service_manager.register_service("gemini", GeminiServiceV2())
            self.service_manager.register_service("salesforce", SalesforceServiceV2())
        except Exception as e:
            self.logger.error(f"서비스 등록 실패: {e}")
    
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
        
        # config에서 기본값
        if lookback_minutes is None:
            lookback_minutes = self.config['WORKFLOW_CONFIG']['EMAIL_LOOKBACK_MINUTES']
        if max_emails is None:
            max_emails = self.config['WORKFLOW_CONFIG']['MAX_EMAILS_PER_CHECK']
        
        # 서비스 상태 확인
        health_status = self.service_manager.health_check()
        if not all(health_status.values()):
            self.logger.warning(f"일부 서비스 상태 불량: {health_status}")
        
        try:
            # 새 이메일 조회
            gmail_service = self.service_manager.get_service("gmail")
            if not gmail_service:
                self.logger.error("Gmail 서비스를 사용할 수 없습니다")
                return []
            
            new_emails = gmail_service.get_recent_emails(lookback_minutes, max_emails)
            
            if not new_emails:
                self.logger.info("처리할 새 이메일 없음")
                return []
            
            # 중복 제거
            unique_emails = [email for email in new_emails 
                           if email.get('id') not in self.processed_emails]
            
            if not unique_emails:
                self.logger.info("모든 이메일이 이미 처리됨")
                return []
            
            self.logger.info(f"🎉 {len(unique_emails)}개 새 이메일 발견")
            
            # 각 이메일 처리
            results = []
            for i, email in enumerate(unique_emails, 1):
                self.logger.info(f"\n{'─' * 60}")
                self.logger.info(f"[{i}/{len(unique_emails)}] 이메일 처리 중")
                self.logger.info(f"{'─' * 60}")
                
                result = self._process_single_email(email)
                if result:
                    results.append(result)
                    self.processed_emails.add(email.get('id'))
            
            self.logger.info(f"\n✅ 이메일 처리 완료: {len(results)}개")
            return results
            
        except Exception as e:
            self.logger.error(f"이메일 처리 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def _process_single_email(self, email: Dict) -> Optional[Dict]:
        """개별 이메일 처리"""
        email_id = email.get('id')
        sender = email.get('sender', '')
        subject = email.get('subject', '')
        content = email.get('content', '')
        
        self.logger.info(f"📧 발신자: {sender}")
        self.logger.info(f"📋 제목: {subject}")
        
        result = {
            'email_id': email_id,
            'sender': sender,
            'subject': subject,
            'processed_at': datetime.now().isoformat(),
            'customer_info': None,
            'level1_result': {'status': 'pending', 'description': '답장 생성 및 발송'},
            'level2_result': {'status': 'pending', 'description': 'Salesforce Lead 생성'}
        }
        
        try:
            # Level 1: 답장 처리 (고객 정보 기반)
            level1_result = self._execute_level1_workflow(sender, subject, content, email_id)
            result['customer_info'] = level1_result.get('customer_info')
            result['level1_result'] = {
                'status': 'success' if level1_result.get('reply_sent') else 'failed',
                'description': '답장 생성 및 발송',
                'reply_sent': level1_result.get('reply_sent', False)
            }
            
            # Level 2: Lead 생성 (정보가 완전한 경우만)
            if result['customer_info'] and result['customer_info'].get('has_all_info'):
                level2_result = self._execute_level2_workflow(result['customer_info'])
                result['level2_result'] = {
                    'status': 'success' if level2_result else 'failed',
                    'description': 'Salesforce Lead 생성',
                    'lead_created': level2_result
                }
            else:
                result['level2_result'] = {
                    'status': 'skipped',
                    'description': '정보 부족으로 Lead 생성 건너뜀',
                    'lead_created': False
                }
            
            self.logger.info("✅ 이메일 처리 완료")
            return result
            
        except Exception as e:
            self.logger.error(f"이메일 처리 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _execute_level1_workflow(self, sender: str, subject: str, content: str, email_id: str) -> Dict:
        """Level 1: 자동 답장 (고객 정보 추출 포함)"""
        self.logger.info("\n🔷 Level 1: 답장 처리 시작")
        
        result = {
            'customer_info': None,
            'reply_sent': False
        }
        
        try:
            gemini_service = self.service_manager.get_service("gemini")
            gmail_service = self.service_manager.get_service("gmail")
            
            if not gemini_service or not gmail_service:
                self.logger.error("필요한 서비스를 사용할 수 없습니다")
                return result
            
            # 1. 고객 정보 추출
            self.logger.info("📋 고객 정보 추출 중...")
            customer_info = gemini_service.extract_customer_info(content, sender)
            result['customer_info'] = customer_info
            
            self.logger.info(f"  이름: {customer_info.get('name')}")
            self.logger.info(f"  회사: {customer_info.get('company')}")
            self.logger.info(f"  직급: {customer_info.get('title')}")
            self.logger.info(f"  전화: {customer_info.get('phone')}")
            self.logger.info(f"  이메일: {customer_info.get('email')}")
            self.logger.info(f"  완전한 정보: {customer_info['has_all_info']}")
            
            # 2. 답변 생성 (조건부)
            self.logger.info("💬 답변 생성 중...")
            reply = gemini_service.generate_reply(customer_info, subject)
            
            if not reply:
                self.logger.error("답변 생성 실패")
                return result
            
            self.logger.info(f"  답변 제목: {reply['subject']}")
            self.logger.info(f"  답변 내용: {reply['body'][:100]}...")
            
            # 3. 답장 발송
            self.logger.info("📤 답장 발송 중...")
            reply_sent = gmail_service.send_reply(
                to_email=customer_info['email'],
                subject=reply['subject'],
                content=reply['body'],
                original_email_id=email_id
            )
            
            result['reply_sent'] = reply_sent
            
            if reply_sent:
                self.logger.info("✅ Level 1 완료: 답장 발송 성공")
            else:
                self.logger.error("❌ Level 1 실패: 답장 발송 실패")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Level 1 실패: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return result
    
    def _execute_level2_workflow(self, customer_info: Dict) -> bool:
        """Level 2: Lead 생성 (정보가 완전한 경우만)"""
        self.logger.info("\n🔷 Level 2: Lead 생성 시작")
        
        try:
            salesforce_service = self.service_manager.get_service("salesforce")
            
            if not salesforce_service:
                self.logger.warning("Salesforce 서비스를 사용할 수 없습니다")
                return False
            
            # Lead 생성
            self.logger.info("👤 Salesforce Lead 생성 중...")
            lead_created = salesforce_service.create_lead(customer_info)
            
            if lead_created:
                self.logger.info("✅ Level 2 완료: Lead 생성 성공")
            else:
                self.logger.error("❌ Level 2 실패: Lead 생성 실패")
            
            return lead_created
            
        except Exception as e:
            self.logger.error(f"Level 2 실패: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_single(self):
        """단일 실행 모드"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("단일 실행 모드 시작")
        self.logger.info("=" * 60)
        
        if not self.initialize():
            self.logger.error("초기화 실패")
            return
        
        results = self.process_new_emails()
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("단일 실행 모드 완료")
        self.logger.info("=" * 60)
        
        return results
    
    def run_monitor(self):
        """모니터링 모드 (지속 실행)"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("모니터링 모드 시작")
        self.logger.info("=" * 60)
        
        if not self.initialize():
            self.logger.error("초기화 실패")
            return
        
        interval = self.config['WORKFLOW_CONFIG']['EMAIL_CHECK_INTERVAL']
        
        self.logger.info(f"📅 이메일 체크 간격: {interval}초")
        self.logger.info("⏹️  Ctrl+C로 중단")
        self.logger.info("=" * 60)
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.logger.info(f"\n[{current_time}] 🔍 체크 #{check_count}")
                
                results = self.process_new_emails()
                
                if results:
                    self.logger.info(f"🎉 {len(results)}개 이메일 처리 완료!")
                else:
                    self.logger.info("✅ 새 이메일 없음")
                
                self.logger.info(f"⏰ 다음 체크: {interval}초 후...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n⏹️  모니터링 중단")
            self.logger.info("=" * 60)
    
    def health_check(self):
        """헬스 체크"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("헬스 체크")
        self.logger.info("=" * 60)
        
        print("\n📊 시스템 상태")
        print("=" * 60)
        
        # 1. 설정 검증
        print("\n1️⃣ 설정 검증...")
        if config.validate_config(self.environment):
            print("   ✅ 설정 정상")
        else:
            print("   ❌ 설정 오류")
        
        # 2. 서비스 초기화
        print("\n2️⃣ 서비스 초기화...")
        if self.initialize():
            health_status = self.service_manager.health_check()
            for service_name, status in health_status.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {service_name}")
        else:
            print("   ❌ 초기화 실패")
        
        # 3. 이메일 조회 테스트
        print("\n3️⃣ 이메일 조회 테스트...")
        try:
            gmail_service = self.service_manager.get_service("gmail")
            if gmail_service:
                emails = gmail_service.get_recent_emails(minutes_ago=60, max_results=5)
                print(f"   ✅ 최근 1시간: {len(emails)}개")
            else:
                print("   ❌ Gmail 서비스 없음")
        except Exception as e:
            print(f"   ❌ 실패: {e}")
        
        print("\n" + "=" * 60)