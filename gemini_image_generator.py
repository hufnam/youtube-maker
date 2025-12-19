# gemini_image_generator.py
"""
Gemini 이미지 생성 모듈
대본에서 각 컷별 이미지 생성을 위한 프롬프트 생성 및 이미지 생성
"""

from google import genai
from google.genai import types
from PIL import Image
import google.generativeai as genai_legacy
from typing import Optional, List, Dict, Tuple
import time
import re
import io
import base64


class GeminiImageGenerator:
    def __init__(self, api_key: str):
        """
        Gemini 이미지 생성기 초기화

        Args:
            api_key: Gemini API 키
        """
        if not api_key or len(api_key) < 10:
            raise ValueError("유효한 Gemini API 키가 필요합니다.")

        self.api_key = api_key

        # 새로운 google-genai 클라이언트 (이미지 생성용)
        self.client = genai.Client(api_key=api_key)

        # 기존 google-generativeai 라이브러리 (텍스트 생성용)
        genai_legacy.configure(api_key=api_key)
        self.text_model = genai_legacy.GenerativeModel('gemini-2.5-flash')

        # 지원 모델
        self.supported_models = {
            "gemini-2.5-flash-image": "Gemini 2.5 Flash (기본, 빠른 생성)",
            "gemini-3-pro-image-preview": "Gemini 3.0 Pro Flash Preview (고품질)"
        }

        self.default_model = "gemini-2.5-flash-image"

    def parse_script_to_cuts(self, script: str) -> List[Dict]:
        """
        대본을 컷 단위로 파싱

        Args:
            script: 전체 대본 텍스트

        Returns:
            List[Dict]: 컷 정보 리스트
        """
        cuts = []

        # 컷 구분 패턴: === CUT 1 (0:00-0:08) === 형식
        cut_pattern = r'===\s*CUT\s*(\d+)\s*\(([^)]+)\)\s*==='

        # 대본을 컷으로 분할
        parts = re.split(cut_pattern, script)

        # parts: [intro, cut_num, time, content, cut_num, time, content, ...]
        i = 1
        while i < len(parts) - 2:
            cut_num = parts[i]
            time_range = parts[i + 1]
            content = parts[i + 2].strip()

            # 컷 내용에서 장면 설명, 대사, 음악 추출
            scene_desc = ""
            narration = ""
            music = ""

            # [장면 설명] 추출
            scene_match = re.search(r'\[장면\s*설명\]\s*\n?(.*?)(?=\[|---|\Z)', content, re.DOTALL)
            if scene_match:
                scene_desc = scene_match.group(1).strip()

            # [대사/내레이션] 추출
            narration_match = re.search(r'\[대사/내레이션\]\s*\n?(.*?)(?=\[|---|\Z)', content, re.DOTALL)
            if narration_match:
                narration = narration_match.group(1).strip()

            # [음악/효과음] 추출
            music_match = re.search(r'\[음악/효과음\]\s*\n?(.*?)(?=\[|---|\Z)', content, re.DOTALL)
            if music_match:
                music = music_match.group(1).strip()

            cuts.append({
                'cut_number': int(cut_num),
                'time_range': time_range,
                'scene_description': scene_desc,
                'narration': narration,
                'music': music,
                'full_content': content
            })

            i += 3

        return cuts

    def generate_image_prompts(
        self,
        cuts: List[Dict],
        style: str = "Animation",
        mood: str = "Cinematic",
        color: str = "Vibrant & Colorful",
        lighting: str = "Natural Sunlight",
        camera: str = "Wide Angle",
        max_retries: int = 3
    ) -> List[Dict]:
        """
        각 컷에 대한 이미지 생성용 영어 프롬프트 생성

        Args:
            cuts: 파싱된 컷 리스트
            style: 스타일 (Realistic Photography, Animation, 3D Pixar Style, etc.)
            mood: 분위기 (Cinematic, Dreamy/Soft, Dark/Moody, etc.)
            color: 색감 (Vibrant & Colorful, Monochrome/B&W, etc.)
            lighting: 조명 (Golden Hour, Neon/Night City, etc.)
            camera: 카메라 (Close-up, Wide Angle, Low Angle, etc.)
            max_retries: 최대 재시도 횟수

        Returns:
            List[Dict]: 이미지 프롬프트가 추가된 컷 리스트
        """
        results = []

        for cut in cuts:
            prompt = self._build_prompt_generation_request(
                cut=cut,
                style=style,
                mood=mood,
                color=color,
                lighting=lighting,
                camera=camera
            )

            image_prompt = None
            for attempt in range(max_retries):
                try:
                    response = self.text_model.generate_content(prompt)
                    image_prompt = response.text.strip()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        image_prompt = f"Error generating prompt: {str(e)}"

            cut_result = cut.copy()
            cut_result['image_prompt'] = image_prompt
            cut_result['generated_image'] = None
            results.append(cut_result)

        return results

    def _build_prompt_generation_request(
        self,
        cut: Dict,
        style: str,
        mood: str,
        color: str,
        lighting: str,
        camera: str
    ) -> str:
        """
        이미지 프롬프트 생성을 위한 요청 프롬프트 구성
        """
        # 스타일 설명 매핑
        style_descriptions = {
            "Realistic Photography": "photorealistic, live action photography, high detail realistic image",
            "Animation": "anime style, 2D animation, illustrated",
            "3D Pixar Style": "3D rendered, Pixar animation style, CGI, stylized 3D characters",
            "Cyberpunk/Futuristic": "cyberpunk aesthetic, futuristic, neon-lit, sci-fi",
            "Cinematic Movie Frame": "cinematic movie still, film grain, widescreen cinematic composition",
            "Oil Painting": "oil painting style, artistic brush strokes, classical painting aesthetic"
        }

        # 색감 설명 매핑
        color_descriptions = {
            "Vibrant & Colorful": "vibrant colors, saturated, colorful",
            "Monochrome/B&W": "black and white, monochrome, grayscale",
            "Pastel/Soft": "pastel colors, soft tones, gentle hues",
            "Warm Earthy Tones": "warm earthy tones, brown, orange, autumn colors",
            "Cool Blue/Teal": "cool blue tones, teal, cyan color palette",
            "High Contrast/Bold": "high contrast, bold colors, dramatic color contrast",
            "Muted/Desaturated": "muted colors, desaturated, subdued palette",
            "Vintage/Sepia": "vintage sepia tone, retro color grading, nostalgic warm tint"
        }

        style_keyword = style_descriptions.get(style, style)
        color_keyword = color_descriptions.get(color, color)

        prompt = f"""You are an expert image prompt engineer for AI image generation.
Based on the following video script scene description, create a detailed image generation prompt in English.

【Scene Information】
Scene Description (Korean): {cut['scene_description']}
Narration (Korean): {cut['narration']}
Time: {cut['time_range']}

【Style Requirements】
- Visual Style: {style_keyword}
- Mood/Atmosphere: {mood}
- Color Palette: {color_keyword}
- Lighting: {lighting}
- Overall Camera Composition: The overall video uses {camera} shots as the primary camera style. Consider this when composing the scene, but you may vary slightly based on what works best for each specific scene.

【Output Requirements】
1. Write the prompt entirely in English
2. Be specific about visual elements, composition, lighting, and atmosphere
3. Include character descriptions if people are mentioned
4. Describe the background and environment in detail
5. Apply the specified style, mood, color, and lighting consistently
6. Keep the prompt concise but comprehensive (2-4 sentences)
7. Do NOT include any explanations, just output the image prompt directly
8. CRITICAL: The image must contain NO TEXT, NO LETTERS, NO WORDS, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS, NO WRITING of any kind. This is a pure visual image without any textual elements.

【Output Format】
Return ONLY the image generation prompt, nothing else. No quotes, no labels, just the prompt text."""

        return prompt

    def generate_single_image(
        self,
        prompt: str,
        model: str = None,
        aspect_ratio: str = "16:9",
        max_retries: int = 3
    ) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        단일 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트 (영어)
            model: 사용할 모델
            aspect_ratio: 이미지 비율 ("16:9" 또는 "9:16")
            max_retries: 최대 재시도 횟수

        Returns:
            Tuple[Image, error_message]: 생성된 이미지와 에러 메시지
        """
        if model is None:
            model = self.default_model

        # 비율에 따른 프롬프트 수정
        # aspect_hint = "wide landscape format, 16:9 aspect ratio" if aspect_ratio == "16:9" else "vertical portrait format, 9:16 aspect ratio"
        # enhanced_prompt = f"{prompt}, {aspect_hint}"

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE'],
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio,
                        )
                    )
                )

                # 응답에서 이미지 추출
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        # 이미지 데이터를 PIL Image로 변환
                        image_data = part.inline_data.data
                        image = Image.open(io.BytesIO(image_data))
                        return image, None

                return None, "이미지가 응답에 포함되지 않았습니다."

            except Exception as e:
                error_msg = str(e)

                # Rate Limit 처리
                if "429" in error_msg or "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 3
                        time.sleep(wait_time)
                        continue

                if attempt == max_retries - 1:
                    return None, f"이미지 생성 실패: {error_msg}"

        return None, "알 수 없는 오류"

    def generate_all_images(
        self,
        cuts_with_prompts: List[Dict],
        model: str = None,
        aspect_ratio: str = "16:9",
        progress_callback=None
    ) -> List[Dict]:
        """
        모든 컷에 대해 이미지 생성

        Args:
            cuts_with_prompts: 이미지 프롬프트가 포함된 컷 리스트
            model: 사용할 모델
            aspect_ratio: 이미지 비율 ("16:9" 또는 "9:16")
            progress_callback: 진행 상황 콜백 함수

        Returns:
            List[Dict]: 이미지가 추가된 컷 리스트
        """
        results = []
        total = len(cuts_with_prompts)

        for i, cut in enumerate(cuts_with_prompts):
            if progress_callback:
                progress_callback(i + 1, total, f"컷 {cut['cut_number']} 이미지 생성 중...")

            image, error = self.generate_single_image(
                prompt=cut['image_prompt'],
                model=model,
                aspect_ratio=aspect_ratio
            )

            cut_result = cut.copy()
            cut_result['generated_image'] = image
            cut_result['image_error'] = error
            results.append(cut_result)

            # API 호출 간 딜레이
            if i < total - 1:
                time.sleep(1)

        return results

    def regenerate_cut_image(
        self,
        cut: Dict,
        new_prompt: str,
        model: str = None,
        aspect_ratio: str = "16:9"
    ) -> Dict:
        """
        특정 컷의 이미지 재생성

        Args:
            cut: 컷 정보
            new_prompt: 새로운 이미지 프롬프트
            model: 사용할 모델
            aspect_ratio: 이미지 비율 ("16:9" 또는 "9:16")

        Returns:
            Dict: 업데이트된 컷 정보
        """
        image, error = self.generate_single_image(prompt=new_prompt, model=model, aspect_ratio=aspect_ratio)

        cut_result = cut.copy()
        cut_result['image_prompt'] = new_prompt
        cut_result['generated_image'] = image
        cut_result['image_error'] = error

        return cut_result

    def test_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = self.text_model.generate_content("Say hello")
            return bool(response and response.text)
        except Exception as e:
            print(f"연결 테스트 실패: {e}")
            return False
