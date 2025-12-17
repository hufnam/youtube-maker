# gemini_script_generator.py
import google.generativeai as genai
from typing import Optional
import time

class GeminiScriptGenerator:
    def __init__(self, api_key: str):
        """
        Gemini 대본 생성기 초기화
        
        Args:
            api_key: Gemini API 키
        """
        if not api_key or len(api_key) < 10:
            raise ValueError("유효한 Gemini API 키가 필요합니다.")
        
        # API 키 설정
        genai.configure(api_key=api_key)
        
        # 모델 초기화 (Gemini 2.5 Flash)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_script(
        self,
        topic: str,
        language: str = "한국어",
        format_type: str = "롱폼",
        duration: int = 1,
        target_audience: str = "20-30대",
        custom_prompt: str = "",
        max_retries: int = 3
    ) -> Optional[str]:
        """
        YouTube 영상 대본 생성 (컷 스토리보드 형식)
        
        Args:
            topic: 영상 주제
            language: 대본 언어 (한국어/영어)
            format_type: 포맷 (롱폼/숏폼)
            duration: 영상 길이 (분)
            target_audience: 대상 시청자
            custom_prompt: 사용자 정의 프롬프트 템플릿 (선택)
            max_retries: 최대 재시도 횟수
            
        Returns:
            str: 생성된 대본 (실패 시 None)
        """
        # 컷 개수 계산 (1분당 10개)
        total_cuts = duration * 10
        
        # 프롬프트 생성
        if custom_prompt:
            # 사용자 정의 템플릿 사용
            prompt = custom_prompt.format(
                topic=topic,
                language=language,
                format_type=format_type,
                duration=duration,
                total_cuts=total_cuts,
                target_audience=target_audience
            )
        else:
            # 기본 템플릿 사용
            prompt = self._build_prompt(
                topic=topic,
                language=language,
                format_type=format_type,
                duration=duration,
                total_cuts=total_cuts,
                target_audience=target_audience
            )
        
        # 재시도 로직으로 대본 생성
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                
                # Rate Limit 오류 처리
                if "429" in error_msg or "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2
                        print(f"Rate limit 도달. {wait_time}초 대기 중...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"API 요청 한도 초과\n\n원본 에러: {error_msg}")
                
                # 기타 오류
                raise Exception(f"{error_msg}")
        
        return None
    
    def _build_prompt(
        self,
        topic: str,
        language: str,
        format_type: str,
        duration: int,
        total_cuts: int,
        target_audience: str
    ) -> str:
        """
        대본 생성용 프롬프트 구성 (롱폼/숏폼 통합)
        
        Returns:
            str: 완성된 프롬프트
        """
        # 언어별 설정
        lang_instruction = "한국어로" if language == "한국어" else "in English"
        
        # 포맷별 특성
        if format_type == "숏폼":
            format_guide = """
【숏폼 특성】
• 처음 1-2초가 가장 중요 (즉각적인 훅)
• 빠른 전개와 강렬한 임팩트
• 짧고 강렬한 문장 사용
• 시각적 요소를 강조
• 명확한 CTA (Call To Action)
• 전체적으로 에너지 넘치고 역동적"""
        else:  # 롱폼
            format_guide = """
【롱폼 특성】
• 자연스러운 도입부로 시작
• 충분한 설명과 예시 제공
• 스토리텔링 요소 포함
• 시청자와의 소통 (질문, 공감 등)
• 깊이 있는 내용 전개
• 적절한 휴지와 강조"""
        
        prompt = f"""당신은 전문 YouTube 영상 대본 작가입니다.
다음 조건에 맞는 컷 단위 스토리보드 형식의 대본을 {lang_instruction} 작성해주세요.

【기본 정보】
• 주제: {topic}
• 언어: {language}
• 포맷: {format_type}
• 총 영상 길이: {duration}분
• 총 컷 개수: {total_cuts}개 (1분당 10개 컷)
• 각 컷 길이: 6-8초
• 대상 시청자: {target_audience}

{format_guide}

【대본 구조 - 컷 스토리보드 형식】
각 컷은 6-8초 분량으로 구성되며, 다음 형식을 정확히 따라주세요:

=== CUT 1 (0:00-0:08) ===
[장면 설명]
화면에 표시될 시각적 요소를 구체적으로 설명

[대사/내레이션]
실제로 말할 내용 (6-8초 안에 자연스럽게 말할 수 있는 분량)

[음악/효과음]
배경음악이나 효과음 제안 (예: 경쾌한 배경음악, 전환 효과음 등)

---

【컷 구성 가이드라인】
• CUT 1-2: 강력한 오프닝 훅 (시청자 주목 확보)
• CUT 3-{total_cuts-2}: 메인 콘텐츠 (주제를 논리적으로 전개)
• CUT {total_cuts-1}-{total_cuts}: 마무리 및 CTA (좋아요, 구독 유도)

【작성 원칙】
1. 각 컷의 대사는 6-8초 안에 자연스럽게 말할 수 있어야 함
2. 장면 설명은 구체적이고 시각적으로 작성
3. 컷 간의 자연스러운 연결과 흐름
4. 시청자의 관심을 끝까지 유지
5. 시간 표기는 정확하게 (예: 0:00-0:08, 0:08-0:16 등)

이제 위의 형식을 정확히 따라 총 {total_cuts}개의 컷으로 구성된 대본을 작성해주세요.
결과는 작성한 대본만 반환해주세요."""
        
        return prompt
    
    def get_default_prompt_template(self) -> str:
        """
        기본 프롬프트 템플릿 반환 (GUI에서 편집 가능하도록)
        
        Returns:
            str: 기본 프롬프트 템플릿
        """
        return """당신은 전문 YouTube 영상 대본 작가입니다.
다음 조건에 맞는 컷 단위 스토리보드 형식의 대본을 작성해주세요.

【기본 정보】
• 주제: {topic}
• 언어: {language}
• 포맷: {format_type}
• 총 영상 길이: {duration}분
• 총 컷 개수: {total_cuts}개 (1분당 10개 컷)
• 각 컷 길이: 6-8초
• 대상 시청자: {target_audience}

【대본 구조 - 컷 스토리보드 형식】
각 컷은 6-8초 분량으로 구성되며, 다음 형식을 정확히 따라주세요:

=== CUT 1 (0:00-0:08) ===
[장면 설명]
화면에 표시될 시각적 요소를 구체적으로 설명

[대사/내레이션]
실제로 말할 내용 (6-8초 안에 자연스럽게 말할 수 있는 분량)

[음악/효과음]
배경음악이나 효과음 제안

---

【작성 원칙】
1. 각 컷의 대사는 6-8초 안에 자연스럽게 말할 수 있어야 함
2. 장면 설명은 구체적이고 시각적으로 작성
3. 컷 간의 자연스러운 연결과 흐름
4. 시청자의 관심을 끝까지 유지

이제 위의 형식을 정확히 따라 총 {total_cuts}개의 컷으로 구성된 대본을 작성해주세요.
결과는 작성한 대본만 반환해주세요."""
    
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = self.model.generate_content("Say hello")
            if not response:
                return False
            try:
                _ = response.text
                return True
            except:
                return True
        except Exception as e:
            error_msg = str(e)
            print(f"연결 테스트 실패: {error_msg}")
            if "api" in error_msg.lower() and "key" in error_msg.lower():
                print("API 키가 올바르지 않습니다.")
            return False