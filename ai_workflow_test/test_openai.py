# ai_workflow_test/test_openai.py
import os
from dotenv import load_dotenv
import requests

load_dotenv("../.env")

def test_openai_api():
    """OpenAI API 연결 테스트"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    print("=" * 60)
    print("OpenAI API 테스트")
    print("=" * 60)
    
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        return False
    
    print(f"✓ API Key 발견: {api_key[:20]}...")
    
    # API 엔드포인트
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "안녕하세요. 간단한 인사말로 답변해주세요."
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print("\n📡 API 요청 중...")
    print(f"   URL: {url}")
    print(f"   Model: gpt-4o-mini")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\n📊 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                text = data['choices'][0]['message']['content']
                print(f"\n✅ OpenAI API 연결 성공!\n")
                print(f"📝 응답 내용:")
                print(f"   {text}")
                print(f"\n💰 토큰 사용량:")
                print(f"   - Prompt: {data['usage']['prompt_tokens']}")
                print(f"   - Completion: {data['usage']['completion_tokens']}")
                print(f"   - Total: {data['usage']['total_tokens']}")
                return True
            else:
                print("❌ 응답 형식이 올바르지 않습니다")
                print(f"   응답: {data}")
                return False
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            
            if response.status_code == 401:
                print("\n⚠️ 401 에러: 인증 실패")
                print("   - API 키가 올바른지 확인하세요")
                print("   - https://platform.openai.com/api-keys")
            elif response.status_code == 429:
                print("\n⚠️ 429 에러: Rate Limit 또는 할당량 초과")
                print("   - 요청 속도를 줄이거나 할당량을 확인하세요")
            
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 성공!")
    else:
        print("❌ 테스트 실패!")
        print("\n확인 사항:")
        print("1. .env 파일에 OPENAI_API_KEY가 설정되어 있는가?")
        print("2. API 키가 올바른가? (sk-proj-... 형식)")
        print("3. OpenAI 계정에 크레딧이 있는가?")
    print("=" * 60)