# scripts/monitor_logs.py - 로그 모니터링

import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque

class LogMonitor:
    """로그 모니터링 클래스"""
    
    def __init__(self, log_file: str = None):
        if log_file is None:
            log_file = Path(__file__).parent.parent / "logs" / "workflow.log"
        self.log_file = Path(log_file)
        self.stats = defaultdict(int)
        self.recent_errors = deque(maxlen=10)
        
    def tail_log(self, lines: int = 20):
        """최근 로그 출력"""
        if not self.log_file.exists():
            print(f"❌ 로그 파일이 없습니다: {self.log_file}")
            return
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in recent_lines:
                print(line.rstrip())
    
    def analyze_logs(self, hours: int = 24):
        """로그 분석"""
        if not self.log_file.exists():
            print(f"❌ 로그 파일이 없습니다: {self.log_file}")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                time_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not time_match:
                    continue
                
                try:
                    log_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                    if log_time < cutoff_time:
                        continue
                except:
                    continue
                
                if 'ERROR' in line:
                    self.stats['errors'] += 1
                    self.recent_errors.append(line.strip())
                elif 'WARNING' in line:
                    self.stats['warnings'] += 1
                elif 'INFO' in line:
                    self.stats['info'] += 1
                
                if '이메일 처리 완료' in line:
                    self.stats['processed_emails'] += 1
        
        self._print_statistics(hours)
    
    def _print_statistics(self, hours: int):
        """통계 출력"""
        print(f"\n📊 지난 {hours}시간 통계:")
        print(f"처리된 이메일: {self.stats['processed_emails']}개")
        print(f"오류: {self.stats['errors']}개")
        print(f"경고: {self.stats['warnings']}개")
        
        if self.recent_errors:
            print(f"\n🚨 최근 오류들:")
            for error in list(self.recent_errors)[-5:]:
                print(f"  {error}")
    
    def watch_logs(self):
        """실시간 로그 감시"""
        print(f"👁️ 실시간 로그 감시 시작: {self.log_file}")
        print("Ctrl+C로 중단")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        if 'ERROR' in line:
                            print(f"🚨 {line.rstrip()}")
                        else:
                            print(line.rstrip())
                    else:
                        time.sleep(0.1)
                        
        except KeyboardInterrupt:
            print("\n모니터링 중단됨")

if __name__ == "__main__":
    import sys
    
    monitor = LogMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'tail':
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            monitor.tail_log(lines)
        elif command == 'analyze':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            monitor.analyze_logs(hours)
        elif command == 'watch':
            monitor.watch_logs()
        else:
            print("사용법: python monitor_logs.py [tail|analyze|watch] [숫자]")
    else:
        print("사용법:")
        print("  python monitor_logs.py tail [라인수]")
        print("  python monitor_logs.py analyze [시간]")
        print("  python monitor_logs.py watch")