# scripts/setup_environment.py - 환경 설정 자동화

import os
import sys
from pathlib import Path

def create_env_template():
    """환경변수 템플릿 파일 생성"""
    template_content = """# Gmail-Gemini-Salesforce 워크플로우 환경변수

# Gemini API 설정
GEMINI_API_KEY=your_gemini_api_key_here

# Salesforce API 설정  
SF_USERNAME=your_salesforce_username@company.com
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token
SF_CLIENT_ID=your_salesforce_consumer_key
SF_CLIENT_SECRET=your_salesforce_consumer_secret
"""
    
    env_template_path = Path(__file__).parent.parent / '.env.template'
    with open(env_template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ .env.template 파일이 생성되었습니다.")

def check_required_files():
    """필수 파일 존재 여부 확인"""
    main_project_root = Path(__file__).parent.parent.parent
    
    required_files = {
        'credentials_new.json': main_project_root / 'credentials_new.json',
        '.env': main_project_root / '.env'
    }
    
    missing_files = []
    for name, file_path in required_files.items():
        if not file_path.exists():
            missing_files.append(f"{name} ({file_path})")
    
    if missing_files:
        print(f"❌ 누락된 파일들: {missing_files}")
        return False
    
    print("✅ 모든 필수 파일이 존재합니다")
    return True

def install_dependencies():
    """필요한 라이브러리 설치"""
    print("📦 필요한 라이브러리 설치 중...")
    
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    if requirements_file.exists():
        os.system(f"pip install -r {requirements_file}")
        print("✅ 라이브러리 설치 완료")
    else:
        print("❌ requirements.txt 파일을 찾을 수 없습니다")

if __name__ == "__main__":
    print("🔧 환경 설정 시작...")
    
    create_env_template()
    install_dependencies() 
    check_required_files()
    
    print("\n🎯 다음 단계:")
    print("1. 상위 폴더의 .env 파일에 실제 API 키 입력")
    print("2. python config.py development 로 설정 검증")
    print("3. python main.py --mode health 로 연결 테스트")