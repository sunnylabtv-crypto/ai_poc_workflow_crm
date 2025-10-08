# ⚡ 빠른 참조

## 자주 사용하는 명령어

```bash
python main.py --mode health                    # 상태 확인
python main.py --mode single                    # 단일 실행
python main.py --mode monitor --env development # 개발 모니터링
python main.py --mode monitor --env production  # 운영 모니터링
```

## Makefile

```bash
make health         # 연결 테스트
make run            # 단일 실행
make monitor        # 개발 모니터링
make logs           # 로그 확인
make watch          # 실시간 로그
```

## 파일 위치

| 파일 | 위치 |
|-----|------|
| 환경변수 | ../.env |
| Gmail 인증 | ../credentials_new.json |
| 로그 | logs/workflow.log |
