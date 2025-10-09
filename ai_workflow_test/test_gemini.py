# test_gemini.py - Gemini API 테스트
import os
from dotenv import load_dotenv
import requests

# .env 파일 로드
load_dotenv("../.env")

def test_gemini_api():
    """Gemini API 연결 테스트"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("=" * 60)
    print("Gemini API 테스트")
    print("=" * 60)
    
    # API 키 확인
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다!")
        return False
    
    print(f"✓ API Key 발견: {api_key[:20]}...")
    
    # API 엔드포인트
    model = "gemini-2.0-flash-lite"
    base_url = "https://generativelanguage.googleapis.com/v1"
    url = f"{base_url}/models/{model}:generateContent"
    
    # 테스트 요청
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "key": api_key
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "안녕하세요. 간단한 인사말로 답변해주세요."
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100
        }
    }
    
    print("\n📡 API 요청 중...")
    print(f"   URL: {url}")
    print(f"   Model: {model}")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            json=payload,
            timeout=30
        )
        
        print(f"\n📊 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"\n✅ Gemini API 연결 성공!\n")
                print(f"📝 응답 내용:")
                print(f"   {text}")
                return True
            else:
                print("❌ 응답 형식이 올바르지 않습니다")
                print(f"   응답: {data}")
                return False
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            
            if response.status_code == 429:
                print("\n⚠️ 429 에러: API 할당량 초과 또는 Rate Limit")
                print("   - API 키가 올바른지 확인하세요")
                print("   - Google AI Studio에서 새 키를 발급받으세요")
                print("   - https://aistudio.google.com/")
            elif response.status_code == 400:
                print("\n⚠️ 400 에러: 잘못된 API 키 또는 요청")
            
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 성공!")
    else:
        print("❌ 테스트 실패!")
        print("\n확인 사항:")
        print("1. .env 파일에 GEMINI_API_KEY가 설정되어 있는가?")
        print("2. API 키가 올바른가? (AIzaSyC... 형식)")
        print("3. Google AI Studio에서 키를 활성화했는가?")
    print("=" * 60)