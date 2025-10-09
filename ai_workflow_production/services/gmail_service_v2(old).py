# services/gmail_service_v2.py - Gmail 서비스

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.base_service import BaseService
from typing import List, Dict, Optional

class GmailServiceV2(BaseService):
    """Gmail API 서비스"""
    
    def __init__(self, config=None):
        super().__init__("Gmail")
        
        # 레거시 서비스 import
        try:
            from ai_workflow_test.test_api_google_gmail_service import GmailService
            # config가 있으면 전달, 없으면 그냥 생성
            if config:
                self._original_service = GmailService(config)
            else:
                self._original_service = GmailService()
        except (ImportError, TypeError) as e:
            self.logger.warning(f"레거시 Gmail 서비스 초기화 실패: {e}")
            self._original_service = None
    
    def authenticate(self) -> bool:
        """Gmail 인증"""
        if self._original_service:
            return self._original_service.authenticate()
        return False
    
    def get_recent_emails(self, minutes_ago: int = 10, max_results: int = 10) -> List[Dict]:
        """최근 이메일 조회"""
        def _get_emails():
            if self._original_service:
                return self._original_service.get_recent_emails(minutes_ago, max_results)
            return []
        
        return self.execute_with_retry("최근 이메일 조회", _get_emails) or []
    
    def send_reply(self, to_email: str, subject: str, content: str, 
                  original_email_id: str = None) -> bool:
        """답장 발송"""
        def _send():
            if self._original_service:
                return self._original_service.send_reply(to_email, subject, content, original_email_id)
            return False
        
        result = self.execute_with_retry("답장 발송", _send)
        return result is not None and result