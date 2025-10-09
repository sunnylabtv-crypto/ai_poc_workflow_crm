# main.py

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ✅ logger_config 임포트 추가
from ai_workflow_production.utils.logger_config import setup_logging
from ai_workflow_production.core.workflow_engine import WorkflowEngine

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Workflow Production')
    parser.add_argument(
        '--mode',
        choices=['single', 'monitor', 'health'],
        default='monitor',
        help='실행 모드: single(단일 실행), monitor(모니터링), health(헬스 체크)'
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production'],
        default='development',
        help='환경 설정: development 또는 production'
    )
    parser.add_argument(
        '--log-rotation',
        choices=['time', 'size'],
        default='time',
        help='로그 로테이션 타입: time(날짜 기반) 또는 size(크기 기반)'
    )

    args = parser.parse_args()

    # ✅ 로깅 설정 (logger_config.py 사용)
    logger = setup_logging(
        app_name="ai_workflow_production",
        rotation_type=args.log_rotation
    )
    
    logger.info(f"실행 모드: {args.mode}")
    logger.info(f"환경: {args.env}")
    logger.info(f"로그 로테이션: {args.log_rotation}")

    # 워크플로우 엔진 시작
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