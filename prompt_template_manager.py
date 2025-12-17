# prompt_template_manager.py
import json
import os
from pathlib import Path
from typing import Optional

class PromptTemplateManager:
    def __init__(self):
        """프롬프트 템플릿 관리자 초기화"""
        # 설정 디렉토리 (.youtube_maker)
        self.config_dir = Path.home() / '.youtube_maker'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 템플릿 파일 경로
        self.template_file = self.config_dir / 'prompt_templates.json'
        
        # 기본 템플릿 로드 또는 생성
        self.templates = self.load_templates()
    
    def get_default_template(self) -> str:
        """기본 프롬프트 템플릿 반환"""
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
최종 결과는 작성한 대본만 반환해주세요."""
    
    def load_templates(self) -> dict:
        """저장된 템플릿 로드"""
        if self.template_file.exists():
            try:
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"템플릿 로드 실패: {e}")
                return {"default": self.get_default_template()}
        else:
            # 기본 템플릿 생성
            default_templates = {"default": self.get_default_template()}
            self.save_templates(default_templates)
            return default_templates
    
    def save_templates(self, templates: dict) -> bool:
        """템플릿 저장"""
        try:
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"템플릿 저장 실패: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[str]:
        """특정 템플릿 가져오기"""
        return self.templates.get(name)
    
    def save_template(self, name: str, template: str) -> bool:
        """새 템플릿 저장"""
        self.templates[name] = template
        return self.save_templates(self.templates)
    
    def delete_template(self, name: str) -> bool:
        """템플릿 삭제 (default는 삭제 불가)"""
        if name == "default":
            return False
        
        if name in self.templates:
            del self.templates[name]
            return self.save_templates(self.templates)
        return False
    
    def get_template_names(self) -> list:
        """모든 템플릿 이름 목록"""
        return list(self.templates.keys())
    
    def reset_to_default(self) -> bool:
        """기본 템플릿으로 리셋"""
        self.templates = {"default": self.get_default_template()}
        return self.save_templates(self.templates)