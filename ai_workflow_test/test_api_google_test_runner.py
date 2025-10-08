from test_api_google_config import Config
from test_api_google_gmail_service import GmailService
from test_api_google_gemini_service import GeminiService

class APITestRunner:
    """API 테스트 러너 클래스"""
    
    def __init__(self):
        """테스트 러너 초기화"""
        self.config = Config()
        self.gmail_service = GmailService(self.config)
        self.gemini_service = GeminiService(self.config)
        
        print("=== API 테스트 러너 초기화 완료 ===")
        self.config.print_status()
    
    def test_environment(self) -> bool:
        """환경 설정 테스트"""
        print("\n=== 환경 설정 테스트 ===")
        return self.config.print_status()
    
    def test_gmail_api(self) -> bool:
        """Gmail API 테스트"""
        print("\n=== Gmail API 테스트 ===")
        return self.gmail_service.test_connection()
    
    def test_gemini_api(self) -> bool:
        """Gemini API 테스트"""
        print("\n=== Gemini API 테스트 ===")
        return self.gemini_service.test_connection()
    
    def test_all_apis(self) -> bool:
        """모든 API 테스트"""
        print("\n=== 전체 API 테스트 ===")
        
        # 환경 확인
        if not self.test_environment():
            return False
        
        # Gmail API 테스트
        gmail_ok = self.test_gmail_api()
        
        # Gemini API 테스트
        gemini_ok = self.test_gemini_api()
        
        if gmail_ok and gemini_ok:
            print("\n🎉 모든 API 테스트 성공!")
            return True
        else:
            print("\n❌ 일부 API 테스트 실패")
            return False
    
    def integrated_workflow_test(self) -> bool:
        """통합 워크플로우 테스트"""
        print("\n=== 통합 워크플로우 테스트 ===")
        print("Gemini AI로 이메일 생성 → Gmail API로 전송")
        
        # 사전 확인
        if not self.config.print_status():
            print("환경 설정을 먼저 완료해주세요.")
            return False
        
        # Gmail 인증
        if not self.gmail_service.authenticate():
            print("Gmail 인증에 실패했습니다.")
            return False
        
        # Gemini 연결 확인
        if not self.gemini_service.test_connection():
            print("Gemini API 연결에 실패했습니다.")
            return False
        
        # 사용자 입력
        topic = input("\n이메일 주제를 입력하세요 (예: 프로젝트 진행 상황 보고): ").strip()
        if not topic:
            topic = "프로젝트 진행 상황 보고"
        
        recipient = input("수신자 이메일을 입력하세요: ").strip()
        if not recipient:
            print("❌ 수신자 이메일이 필요합니다.")
            return False
        
        # Gemini로 이메일 생성
        print(f"\nGemini AI로 '{topic}' 주제의 이메일을 생성하는 중...")
        email_data = self.gemini_service.generate_email_content(topic)
        
        if not email_data:
            print("❌ 이메일 생성 실패")
            return False
        
        print(f"\n생성된 이메일:")
        print(f"제목: {email_data['subject']}")
        print(f"내용:\n{email_data['body']}")
        
        # 전송 확인
        confirm = input("\n이 이메일을 전송하시겠습니까? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("전송을 취소했습니다.")
            return True
        
        # Gmail로 전송
        print("\nGmail API로 이메일을 전송하는 중...")
        success = self.gmail_service.send_email(
            recipient, 
            email_data['subject'], 
            email_data['body']
        )
        
        if success:
            print("🎉 통합 워크플로우 테스트 완료!")
            print("   Gemini AI 이메일 생성 → Gmail API 전송 성공")
            return True
        else:
            print("❌ 통합 워크플로우 테스트 실패")
            return False
    
    def interactive_test_menu(self):
        """대화형 테스트 메뉴"""
        while True:
            print("\n" + "="*50)
            print("API 테스트 메뉴")
            print("="*50)
            print("1. 환경 설정 확인")
            print("2. Gmail API 테스트")
            print("3. Gemini API 테스트")
            print("4. 전체 API 테스트")
            print("5. Gemini 텍스트 생성 테스트")
            print("6. Gmail 이메일 전송 테스트")
            print("7. 통합 워크플로우 테스트 (AI 이메일 생성 + 전송)")
            print("8. 종료")
            print("-" * 50)
            
            choice = input("선택하세요 (1-8): ").strip()
            
            if choice == "1":
                self.test_environment()
                
            elif choice == "2":
                self.test_gmail_api()
                
            elif choice == "3":
                self.test_gemini_api()
                
            elif choice == "4":
                self.test_all_apis()
                
            elif choice == "5":
                prompt = input("Gemini에게 할 질문을 입력하세요: ").strip()
                if prompt:
                    print("\n생성 중...")
                    response = self.gemini_service.generate_text(prompt)
                    if response:
                        print(f"\nGemini 응답:\n{response}")
                        
            elif choice == "6":
                if not self.gmail_service.service:
                    print("먼저 Gmail API 테스트를 실행해주세요.")
                    continue
                    
                to_email = input("수신자 이메일: ").strip()
                subject = input("제목: ").strip()
                body = input("내용: ").strip()
                
                if to_email and subject and body:
                    self.gmail_service.send_email(to_email, subject, body)
                else:
                    print("모든 필드를 입력해주세요.")
                    
            elif choice == "7":
                self.integrated_workflow_test()
                
            elif choice == "8":
                print("프로그램을 종료합니다.")
                break
                
            else:
                print("잘못된 선택입니다. 1-8 중에서 선택하세요.")

def main():
    """메인 실행 함수"""
    print("Gmail & Gemini API 테스트 도구")
    print("=" * 50)
    
    runner = APITestRunner()
    
    print("\n실행 모드를 선택하세요:")
    print("1. 자동 전체 테스트")
    print("2. 통합 워크플로우 테스트")
    print("3. 대화형 테스트 메뉴")
    
    choice = input("선택하세요 (1-3): ").strip()
    
    if choice == "1":
        runner.test_all_apis()
    elif choice == "2":
        runner.integrated_workflow_test()
    else:
        runner.interactive_test_menu()

if __name__ == "__main__":
    main()