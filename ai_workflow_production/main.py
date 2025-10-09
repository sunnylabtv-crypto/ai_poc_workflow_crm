# main.py

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# 이 부분이 core 폴더를 찾을 수 있게 해줍니다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
# ❌ 자체 WorkflowEngine 대신 core의 엔진을 가져옵니다.
from ai_workflow_production.core.workflow_engine import WorkflowEngine

# 로깅 설정 (기존과 동일)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/workflow.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ❌ main.py 내부에 있던 자체 WorkflowEngine 클래스는 전부 삭제합니다.


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Workflow Production')
    parser.add_argument(
        '--mode',
        choices=['single', 'monitor', 'health'],
        default='monitor',  # 기본값을 monitor로 변경하면 편합니다.
        help='실행 모드: single(단일 실행), monitor(모니터링), health(헬스 체크)'
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production'],
        default='development',
        help='환경 설정: development 또는 production'
    )

    args = parser.parse_args()

    # 이제 이 engine은 core/workflow_engine.py의 강력한 엔진입니다.
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