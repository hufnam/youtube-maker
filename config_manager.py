# config_manager.py
"""
API 키 및 설정 관리 모듈
YouTube API 키와 Gemini API 키를 별도로 관리
"""

import os
import json
import base64
from pathlib import Path


class ConfigManager:
    def __init__(self):
        """설정 관리자 초기화"""
        # 사용자 홈 디렉토리에 설정 폴더 생성
        self.config_dir = Path.home() / '.youtube_maker'
        self.config_file = self.config_dir / 'config.json'
        
        # 설정 디렉토리가 없으면 생성
        self.config_dir.mkdir(exist_ok=True)
        
    def _encode_key(self, key: str) -> str:
        """API 키를 간단히 인코딩 (보안 강화)"""
        if not key:
            return ""
        return base64.b64encode(key.encode()).decode()
    
    def _decode_key(self, encoded_key: str) -> str:
        """인코딩된 API 키를 디코딩"""
        if not encoded_key:
            return ""
        try:
            return base64.b64decode(encoded_key.encode()).decode()
        except Exception:
            return ""
    
    # ========== YouTube API 키 관리 ==========
    
    def save_youtube_api_key(self, api_key: str) -> bool:
        """
        YouTube API 키를 파일에 저장
        
        Args:
            api_key: YouTube API 키
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            config = self.load_config()
            config['youtube_api_key'] = self._encode_key(api_key)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"YouTube API 키 저장 실패: {e}")
            return False
    
    def load_youtube_api_key(self) -> str:
        """
        저장된 YouTube API 키를 로드
        
        Returns:
            str: YouTube API 키 (없으면 빈 문자열)
        """
        try:
            config = self.load_config()
            encoded_key = config.get('youtube_api_key', '')
            return self._decode_key(encoded_key)
        except Exception:
            return ""
    
    def has_youtube_api_key(self) -> bool:
        """
        저장된 YouTube API 키가 있는지 확인
        
        Returns:
            bool: YouTube API 키 존재 여부
        """
        api_key = self.load_youtube_api_key()
        return bool(api_key and len(api_key) > 10)
    
    def clear_youtube_api_key(self) -> bool:
        """
        저장된 YouTube API 키 삭제
        
        Returns:
            bool: 삭제 성공 여부
        """
        return self.save_youtube_api_key("")
    
    # ========== Gemini API 키 관리 ==========
    
    def save_gemini_api_key(self, api_key: str) -> bool:
        """
        Gemini API 키를 파일에 저장
        
        Args:
            api_key: Gemini API 키
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            config = self.load_config()
            config['gemini_api_key'] = self._encode_key(api_key)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Gemini API 키 저장 실패: {e}")
            return False
    
    def load_gemini_api_key(self) -> str:
        """
        저장된 Gemini API 키를 로드
        
        Returns:
            str: Gemini API 키 (없으면 빈 문자열)
        """
        try:
            config = self.load_config()
            encoded_key = config.get('gemini_api_key', '')
            return self._decode_key(encoded_key)
        except Exception:
            return ""
    
    def has_gemini_api_key(self) -> bool:
        """
        저장된 Gemini API 키가 있는지 확인
        
        Returns:
            bool: Gemini API 키 존재 여부
        """
        api_key = self.load_gemini_api_key()
        return bool(api_key and len(api_key) > 10)
    
    def clear_gemini_api_key(self) -> bool:
        """
        저장된 Gemini API 키 삭제
        
        Returns:
            bool: 삭제 성공 여부
        """
        return self.save_gemini_api_key("")
    
    # ========== 호환성 유지 (기존 코드용) ==========
    
    def save_api_key(self, api_key: str) -> bool:
        """
        YouTube API 키 저장 (하위 호환성)
        """
        return self.save_youtube_api_key(api_key)
    
    def load_api_key(self) -> str:
        """
        YouTube API 키 로드 (하위 호환성)
        """
        return self.load_youtube_api_key()
    
    def has_api_key(self) -> bool:
        """
        YouTube API 키 존재 확인 (하위 호환성)
        """
        return self.has_youtube_api_key()
    
    def clear_api_key(self) -> bool:
        """
        YouTube API 키 삭제 (하위 호환성)
        """
        return self.clear_youtube_api_key()
    
    # ========== 공통 메서드 ==========
    
    def load_config(self) -> dict:
        """
        전체 설정 로드
        
        Returns:
            dict: 설정 딕셔너리
        """
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_setting(self, key: str, value) -> bool:
        """
        개별 설정 저장
        
        Args:
            key: 설정 키
            value: 설정 값
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            config = self.load_config()
            config[key] = value
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
    
    def get_setting(self, key: str, default=None):
        """
        개별 설정 로드
        
        Args:
            key: 설정 키
            default: 기본값
            
        Returns:
            설정 값 (없으면 기본값)
        """
        config = self.load_config()
        return config.get(key, default)
    
    def clear_all(self) -> bool:
        """
        모든 설정 삭제
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except Exception as e:
            print(f"설정 삭제 실패: {e}")
            return False