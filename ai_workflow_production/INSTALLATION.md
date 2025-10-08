# 📦 설치 가이드

## ⚠️ 중요: Artifact 코드 수동 저장 필요

다음 파일들을 Claude Artifacts에서 복사해서 저장하세요:

### Artifact 1: improved_modular_architecture
- [ ] services/base_service.py
- [ ] services/service_manager.py
- [ ] services/gmail_service_v2.py
- [ ] services/gemini_service_v2.py
- [ ] services/salesforce_service_v2.py
- [ ] core/workflow_engine.py
- [ ] utils/logger_config.py

### Artifact 2: improved_main
- [ ] main.py
- [ ] scripts/setup_environment.py
- [ ] scripts/monitor_logs.py

### Artifact 3: missing_files_package
- [ ] scripts/create_systemd_service.py

### Artifact 4: api_guide_docs
- [ ] docs/API_GUIDE.md

### Artifact 5: config_file
- [ ] config.py ⚠️ 경로 수정 필요!

## config.py 경로 수정

파일 맨 앞에 다음 코드 추가:

```python
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
MAIN_PROJECT_ROOT = PROJECT_ROOT.parent

SHARED_ENV_FILE = MAIN_PROJECT_ROOT / ".env"
SHARED_CREDENTIALS = MAIN_PROJECT_ROOT / "credentials_new.json"
SHARED_TOKEN = MAIN_PROJECT_ROOT / "token_new.json"

load_dotenv(SHARED_ENV_FILE)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Gmail 설정
GMAIL_CONFIG = {
    'CREDENTIALS_FILE': str(SHARED_CREDENTIALS),
    'TOKEN_FILE': str(SHARED_TOKEN),
    # ... 나머지 설정
}
```

## 설치

```bash
pip install -r requirements.txt
python config.py development
python main.py --mode health
```
