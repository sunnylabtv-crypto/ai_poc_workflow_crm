# services/service_manager.py - 서비스 관리자

import logging
from typing import Dict, Optional

class ServiceManager:
    """서비스 관리자 - 여러 서비스를 통합 관리"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, object] = {}
    
    def register_service(self, name: str, service: object) -> None:
        """서비스 등록"""
        self._services[name] = service
        self.logger.info(f"서비스 등록: {name}")
    
    def get_service(self, name: str) -> Optional[object]:
        """서비스 가져오기"""
        service = self._services.get(name)
        if not service:
            self.logger.error(f"서비스를 찾을 수 없음: {name}")
        return service
    
    def initialize_all(self) -> bool:
        """모든 서비스 초기화"""
        self.logger.info("모든 서비스 초기화 시작...")
        
        success_count = 0
        fail_count = 0
        
        for name, service in self._services.items():
            try:
                self.logger.info(f"초기화 중: {name}")
                
                # authenticate 메서드가 있으면 호출
                if hasattr(service, 'authenticate'):
                    if service.authenticate():
                        self.logger.info(f"✅ {name} 초기화 성공")
                        success_count += 1
                    else:
                        self.logger.warning(f"⚠️ {name} 인증 실패")
                        fail_count += 1
                else:
                    # authenticate가 없으면 성공으로 간주
                    self.logger.info(f"✅ {name} 등록 완료")
                    success_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ {name} 초기화 실패: {e}")
                fail_count += 1
        
        self.logger.info(f"초기화 완료: 성공 {success_count}개, 실패 {fail_count}개")
        
        # 최소 1개 이상 성공하면 True
        return success_count > 0
    
    def health_check(self) -> Dict[str, bool]:
        """모든 서비스 상태 확인"""
        health_status = {}
        
        for name, service in self._services.items():
            try:
                # 서비스가 None이 아니면 OK
                health_status[name] = service is not None
            except Exception as e:
                self.logger.error(f"상태 확인 실패 ({name}): {e}")
                health_status[name] = False
        
        return health_status
    
    def get_all_services(self) -> Dict[str, object]:
        """모든 서비스 목록 반환"""
        return self._services.copy()