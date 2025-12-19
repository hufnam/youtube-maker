# music_image_generator.py
"""
음악 이미지 생성 모듈
가사에서 각 줄별 이미지 생성을 위한 프롬프트 생성 및 이미지 생성
"""

from google import genai
from google.genai import types
from PIL import Image
import google.generativeai as genai_legacy
from typing import Optional, List, Dict, Tuple
import time
import io


class MusicImageGenerator:
    def __init__(self, api_key: str):
        """
        음악 이미지 생성기 초기화

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

        # 스타일 설명 매핑
        self.style_descriptions = {
            "Realistic Photography": "photorealistic, live action photography, high detail realistic image",
            "Animation": "anime style, 2D animation, illustrated",
            "3D Pixar Style": "3D rendered, Pixar animation style, CGI, stylized 3D characters",
            "Cyberpunk/Futuristic": "cyberpunk aesthetic, futuristic, neon-lit, sci-fi",
            "Cinematic Movie Frame": "cinematic movie still, film grain, widescreen cinematic composition",
            "Oil Painting": "oil painting style, artistic brush strokes, classical painting aesthetic"
        }

        # 색감 설명 매핑
        self.color_descriptions = {
            "Vibrant & Colorful": "vibrant colors, saturated, colorful",
            "Monochrome/B&W": "black and white, monochrome, grayscale",
            "Pastel/Soft": "pastel colors, soft tones, gentle hues",
            "Warm Earthy Tones": "warm earthy tones, brown, orange, autumn colors",
            "Cool Blue/Teal": "cool blue tones, teal, cyan color palette",
            "High Contrast/Bold": "high contrast, bold colors, dramatic color contrast",
            "Muted/Desaturated": "muted colors, desaturated, subdued palette",
            "Vintage/Sepia": "vintage sepia tone, retro color grading, nostalgic warm tint"
        }

        # 템포 설명 매핑
        self.tempo_descriptions = {
            "Slow": "slow, gentle movement, peaceful pace",
            "Moderate": "moderate tempo, balanced rhythm",
            "Fast": "fast paced, dynamic movement, energetic",
            "Intense": "intense, powerful, dramatic action"
        }

        # 음악 무드 설명 매핑
        self.music_mood_descriptions = {
            "Euphoric/Uplifting": "euphoric, uplifting, joyful atmosphere",
            "Melancholic/Emotional": "melancholic, emotional, touching, bittersweet",
            "Dreamy/Ethereal": "dreamy, ethereal, floating, surreal",
            "Dark/Intense": "dark, intense, dramatic, powerful",
            "Calm/Peaceful": "calm, peaceful, serene, tranquil",
            "Romantic/Sentimental": "romantic, sentimental, warm, intimate",
            "Mysterious/Enigmatic": "mysterious, enigmatic, intriguing, atmospheric"
        }

        # 장르 옵션
        self.genre_options = [
            "Pop", "K-Pop", "Jazz/Blues", "Folk", "R&B", "Hip-Hop",
            "Rock/Alternative", "EDM", "Classical/Orchestral", "Ambient/Chill"
        ]

        # 템포 옵션
        self.tempo_options = ["Slow", "Moderate", "Fast", "Intense"]

        # 곡 무드 옵션
        self.mood_options = [
            "Euphoric/Uplifting", "Melancholic/Emotional", "Dreamy/Ethereal",
            "Dark/Intense", "Calm/Peaceful", "Romantic/Sentimental", "Mysterious/Enigmatic"
        ]

    def parse_lyrics_to_cuts(self, lyrics: str) -> List[Dict]:
        """
        가사를 컷 단위로 파싱 (줄바꿈 기준)

        Args:
            lyrics: 전체 가사 텍스트

        Returns:
            List[Dict]: 컷 정보 리스트
        """
        cuts = []
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]

        for i, line in enumerate(lines):
            cuts.append({
                'cut_number': i + 1,
                'lyrics': line,
                'image_prompt': None,
                'generated_image': None,
                'image_error': None
            })

        return cuts

    def generate_image_prompt(
        self,
        lyric_line: str,
        song_title: str = "",
        visual_concept: str = "",
        genre: str = "Pop",
        tempo: str = "Moderate",
        music_mood: str = "Euphoric/Uplifting",
        style: str = "Animation",
        visual_mood: str = "Cinematic",
        color: str = "Vibrant & Colorful",
        lighting: str = "Natural Sunlight",
        camera: str = "Wide Angle",
        max_retries: int = 3
    ) -> str:
        """
        가사 기반 이미지 생성 프롬프트 생성

        Args:
            lyric_line: 가사 한 줄
            song_title: 곡 제목
            visual_concept: 비주얼 컨셉/테마
            genre: 장르
            tempo: 템포
            music_mood: 곡 무드
            style: 스타일
            visual_mood: 분위기
            color: 색감
            lighting: 조명
            camera: 카메라
            max_retries: 최대 재시도 횟수

        Returns:
            str: 이미지 생성용 영어 프롬프트
        """
        style_keyword = self.style_descriptions.get(style, style)
        color_keyword = self.color_descriptions.get(color, color)
        tempo_keyword = self.tempo_descriptions.get(tempo, tempo)
        mood_keyword = self.music_mood_descriptions.get(music_mood, music_mood)

        prompt = f"""You are an expert image prompt engineer for AI image generation.
Create a detailed image generation prompt for a music video visual based on the following lyrics and music information.

【Lyrics Line】
{lyric_line}

【Music Information】
- Song Title: {song_title if song_title else 'Not specified'}
- Genre: {genre}
- Tempo: {tempo_keyword}
- Mood: {mood_keyword}
- Visual Concept/Theme: {visual_concept if visual_concept else 'Create appropriate visuals based on the lyrics'}

【Visual Style Requirements】
- Visual Style: {style_keyword}
- Atmosphere: {visual_mood}
- Color Palette: {color_keyword}
- Lighting: {lighting}
- Camera: {camera}

【Output Requirements】
1. Write the prompt entirely in English
2. Create a vivid visual scene that represents the emotion and meaning of the lyrics
3. Incorporate the music's mood, tempo, and genre into the visual atmosphere
4. If visual concept is provided, integrate it with the lyrics meaning
5. Include specific details about composition, colors, lighting, and atmosphere
6. Keep the prompt concise but comprehensive (2-4 sentences)
7. Do NOT include any explanations, just output the image prompt directly
8. CRITICAL: The image must contain NO TEXT, NO LETTERS, NO WORDS, NO CAPTIONS, NO SUBTITLES, NO WATERMARKS, NO WRITING of any kind. This is a pure visual image without any textual elements.

【Output Format】
Return ONLY the image generation prompt, nothing else. No quotes, no labels, just the prompt text."""

        for attempt in range(max_retries):
            try:
                response = self.text_model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    # 기본 프롬프트 반환
                    return f"{style_keyword}, {lyric_line}, {mood_keyword}, {color_keyword}, {lighting} lighting, {camera} shot"

    def generate_all_prompts(
        self,
        cuts: List[Dict],
        song_title: str = "",
        visual_concept: str = "",
        genre: str = "Pop",
        tempo: str = "Moderate",
        music_mood: str = "Euphoric/Uplifting",
        style: str = "Animation",
        visual_mood: str = "Cinematic",
        color: str = "Vibrant & Colorful",
        lighting: str = "Natural Sunlight",
        camera: str = "Wide Angle",
        progress_callback=None
    ) -> List[Dict]:
        """
        모든 컷에 대해 이미지 프롬프트 생성

        Args:
            cuts: 파싱된 컷 리스트
            song_title: 곡 제목
            visual_concept: 비주얼 컨셉/테마
            genre: 장르
            tempo: 템포
            music_mood: 곡 무드
            style: 스타일
            visual_mood: 분위기
            color: 색감
            lighting: 조명
            camera: 카메라
            progress_callback: 진행 상황 콜백 함수

        Returns:
            List[Dict]: 이미지 프롬프트가 추가된 컷 리스트
        """
        results = []
        total = len(cuts)

        for i, cut in enumerate(cuts):
            if progress_callback:
                progress_callback(i + 1, total, f"컷 {cut['cut_number']} 프롬프트 생성 중...")

            image_prompt = self.generate_image_prompt(
                lyric_line=cut['lyrics'],
                song_title=song_title,
                visual_concept=visual_concept,
                genre=genre,
                tempo=tempo,
                music_mood=music_mood,
                style=style,
                visual_mood=visual_mood,
                color=color,
                lighting=lighting,
                camera=camera
            )

            cut_result = cut.copy()
            cut_result['image_prompt'] = image_prompt
            results.append(cut_result)

        return results

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
        except Exception:
            return False
