# services/base_service.py - 기본 서비스 클래스

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time

class BaseService(ABC):
    """모든 서비스의 기본 클래스"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        self._authenticated = False
        self._last_auth_time = 0
        self.auth_timeout = 3600  # 1시간
    
    @abstractmethod
    def authenticate(self) -> bool:
        """서비스 인증 (각 서비스에서 구현)"""
        pass
    
    def is_authenticated(self) -> bool:
        """인증 상태 확인 (토큰 만료 고려)"""
        if not self._authenticated:
            return False
        
        if time.time() - self._last_auth_time > self.auth_timeout:
            self.logger.info(f"{self.service_name} 인증 토큰 만료, 재인증 필요")
            return False
            
        return True
    
    def ensure_authenticated(self) -> bool:
        """인증 보장 (필요시 재인증)"""
        if self.is_authenticated():
            return True
        
        self.logger.info(f"{self.service_name} 인증 시작...")
        success = self.authenticate()
        
        if success:
            self._authenticated = True
            self._last_auth_time = time.time()
            self.logger.info(f"{self.service_name} 인증 성공")
        else:
            self.logger.error(f"{self.service_name} 인증 실패")
        
        return success
    
    def execute_with_retry(self, operation_name: str, operation_func, 
                          max_retries: int = 3, retry_delay: int = 1) -> Optional[Any]:
        """재시도 로직이 포함된 작업 실행"""
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"{operation_name} 실행 (시도 {attempt + 1}/{max_retries})")
                result = operation_func()
                self.logger.info(f"{operation_name} 성공")
                return result
                
            except Exception as e:
                self.logger.warning(f"{operation_name} 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    
                    if "auth" in str(e).lower() or "token" in str(e).lower():
                        self.logger.info("인증 오류로 인한 재인증 시도")
                        self.ensure_authenticated()
        
        self.logger.error(f"{operation_name} 최종 실패 (모든 재시도 소진)")
        return None