# utils/logger_config.py - 통합 로깅 설정

import logging
import logging.handlers
import sys
from pathlib import Path

def setup_logging(app_name: str = "WorkflowApp"):
    """통합 로깅 설정"""
    
    # 로그 디렉토리 설정
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "workflow.log"
    
    # 기존 핸들러 제거 (중복 방지)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # 로그 레벨 설정
    log_level = logging.INFO
    
    # 로그 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (로테이션)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 루트 로거 설정
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 앱 로거 반환
    app_logger = logging.getLogger(app_name)
    app_logger.info(f"{app_name} 로깅 초기화 완료")
    
    return app_logger