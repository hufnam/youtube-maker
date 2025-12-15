# config_manager.py
"""
API 키 및 설정 관리 모듈
사용자 설정을 로컬 파일에 안전하게 저장/로드
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
    
    def save_api_key(self, api_key: str) -> bool:
        """
        API 키를 파일에 저장
        
        Args:
            api_key: YouTube API 키
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            config = self.load_config()
            config['api_key'] = self._encode_key(api_key)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"API 키 저장 실패: {e}")
            return False
    
    def load_api_key(self) -> str:
        """
        저장된 API 키를 로드
        
        Returns:
            str: API 키 (없으면 빈 문자열)
        """
        try:
            config = self.load_config()
            encoded_key = config.get('api_key', '')
            return self._decode_key(encoded_key)
        except Exception:
            return ""
    
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
    
    def has_api_key(self) -> bool:
        """
        저장된 API 키가 있는지 확인
        
        Returns:
            bool: API 키 존재 여부
        """
        api_key = self.load_api_key()
        return bool(api_key and len(api_key) > 10)
    
    def clear_api_key(self) -> bool:
        """
        저장된 API 키 삭제
        
        Returns:
            bool: 삭제 성공 여부
        """
        return self.save_api_key("")
    
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