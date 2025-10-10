# config.py - 통합 설정 관리 (공유 파일 경로 사용)

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent  # ai_workflow_production/
MAIN_PROJECT_ROOT = PROJECT_ROOT.parent  # ai_poc_workflow_crm/

# 공유 설정 파일 경로 (상위 폴더)
SHARED_ENV_FILE = MAIN_PROJECT_ROOT / ".env"
SHARED_CREDENTIALS = MAIN_PROJECT_ROOT / "credentials_new.json"
SHARED_TOKEN = MAIN_PROJECT_ROOT / "token_new.json"

# 환경변수 로드 (공유 .env 파일에서)
load_dotenv(SHARED_ENV_FILE)

# 로그 디렉토리 (현재 프로젝트 내)
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Gmail 설정 (공유 파일 경로 사용)
GMAIL_CONFIG = {
    'TARGET_EMAIL': 'sunnylabtv@gmail.com',
    'SCOPES': [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ],
    'CREDENTIALS_FILE': str(SHARED_CREDENTIALS),  # 공유 파일
    'TOKEN_FILE': str(SHARED_TOKEN),              # 공유 파일
    'MAX_RESULTS_PER_QUERY': 50
}

# Gemini API 설정
GEMINI_CONFIG = {
    'API_KEY_ENV': 'GEMINI_API_KEY',
    'MODEL': 'gemini-2.5-flash-lite',
    'BASE_URL': 'https://generativelanguage.googleapis.com/v1',
    'MAX_TOKENS': 2048,
    'TEMPERATURE': 0.7
}

# Salesforce 설정
SALESFORCE_CONFIG = {
    'USERNAME_ENV': 'SF_USERNAME',
    'PASSWORD_ENV': 'SF_PASSWORD',
    'SECURITY_TOKEN_ENV': 'SF_SECURITY_TOKEN',
    'CONSUMER_KEY_ENV': 'SF_CLIENT_ID',
    'CONSUMER_SECRET_ENV': 'SF_CLIENT_SECRET',
    'API_VERSION': '58.0',
    'DEFAULT_SANDBOX': True,
    'DEFAULT_LEAD_SOURCE': 'Email Inquiry',
    'DEFAULT_LEAD_STATUS': 'Open - Not Contacted'
}

# 워크플로우 설정
WORKFLOW_CONFIG = {
    'EMAIL_CHECK_INTERVAL': 300,        # 5분
    'MAX_EMAILS_PER_CHECK': 10,
    'EMAIL_LOOKBACK_MINUTES': 15,
    'RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 5
}

# 로깅 설정
LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'LOG_FILE': str(LOGS_DIR / 'workflow.log'),
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'BACKUP_COUNT': 5
}

# 환경별 설정
ENVIRONMENT_CONFIGS = {
    'development': {
        'WORKFLOW_CONFIG': {
            'EMAIL_CHECK_INTERVAL': 60,      # 1분
            'MAX_EMAILS_PER_CHECK': 5,
            'EMAIL_LOOKBACK_MINUTES': 5
        },
        'LOGGING_CONFIG': {
            'LEVEL': 'DEBUG'
        },
        'SALESFORCE_CONFIG': {
            'DEFAULT_SANDBOX': True
        }
    },
    'production': {
        'WORKFLOW_CONFIG': {
            'EMAIL_CHECK_INTERVAL': 300,     # 5분
            'MAX_EMAILS_PER_CHECK': 15,
            'EMAIL_LOOKBACK_MINUTES': 15
        },
        'LOGGING_CONFIG': {
            'LEVEL': 'INFO'
        },
        'SALESFORCE_CONFIG': {
            'DEFAULT_SANDBOX': False
        }
    }
}

def get_env_variable(var_name: str, default: str = None, required: bool = True) -> str:
    """환경변수 안전하게 가져오기"""
    value = os.getenv(var_name, default)
    if required and value is None:
        raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {var_name}")
    return value

def load_environment_config(environment: str = 'development'):
    """환경별 설정 로드"""
    if environment not in ENVIRONMENT_CONFIGS:
        raise ValueError(f"지원되지 않는 환경: {environment}")
    
    config = {
        'GMAIL_CONFIG': GMAIL_CONFIG.copy(),
        'GEMINI_CONFIG': GEMINI_CONFIG.copy(),
        'SALESFORCE_CONFIG': SALESFORCE_CONFIG.copy(),
        'WORKFLOW_CONFIG': WORKFLOW_CONFIG.copy(),
        'LOGGING_CONFIG': LOGGING_CONFIG.copy()
    }
    
    env_overrides = ENVIRONMENT_CONFIGS[environment]
    for section_name, overrides in env_overrides.items():
        if section_name in config:
            config[section_name].update(overrides)
    
    return config

def validate_config(environment: str = 'development') -> bool:
    """설정 유효성 검사"""
    try:
        print(f"🔍 {environment} 환경 설정 검증 중...")
        
        # 공유 파일 확인
        print(f"\n📁 공유 설정 파일 경로:")
        print(f"  .env: {SHARED_ENV_FILE}")
        print(f"  credentials: {SHARED_CREDENTIALS}")
        print(f"  token: {SHARED_TOKEN}")
        
        if not SHARED_ENV_FILE.exists():
            print(f"❌ .env 파일이 없습니다: {SHARED_ENV_FILE}")
            return False
        
        if not SHARED_CREDENTIALS.exists():
            print(f"❌ credentials 파일이 없습니다: {SHARED_CREDENTIALS}")
            return False
        
        # 환경변수 확인
        required_vars = [
            GEMINI_CONFIG['API_KEY_ENV']
        ]
        
        missing_vars = []
        for var_name in required_vars:
            if not os.getenv(var_name):
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ 누락된 환경변수: {missing_vars}")
            return False
        
        print("✅ 모든 설정이 올바르게 구성되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 설정 검증 중 오류: {e}")
        return False

if __name__ == "__main__":
    import sys
    env = sys.argv[1] if len(sys.argv) > 1 else 'development'
    
    if validate_config(env):
        print(f"\n📊 {env.upper()} 환경 설정 요약:")
        config = load_environment_config(env)
        print(f"이메일 체크 간격: {config['WORKFLOW_CONFIG']['EMAIL_CHECK_INTERVAL']}초")
        print(f"최대 이메일 처리: {config['WORKFLOW_CONFIG']['MAX_EMAILS_PER_CHECK']}개")
        print(f"로그 레벨: {config['LOGGING_CONFIG']['LEVEL']}")
    else:
        print("설정 검증 실패")
        sys.exit(1)