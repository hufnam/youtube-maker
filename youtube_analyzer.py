# youtube_analyzer.py
import os
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from typing import List, Dict, Optional, Tuple
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

class YouTubeTrendAnalyzer:
    def __init__(self, api_key: str):
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("유효한 YouTube API 키가 필요합니다.")
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        self.category_mapping = {
            '전체': None,
            '영화 및 애니메이션': '1',
            '자동차 및 차량': '2',
            '음악': '10',
            '애완동물 및 동물': '15',
            '스포츠': '17',
            '여행 및 이벤트': '19',
            '게임': '20',
            '인물 및 블로그': '22',
            '코미디': '23',
            '엔터테인먼트': '24',
            '뉴스 및 정치': '25',
            '노하우 및 스타일': '26',
            '교육': '27',
            '과학 기술': '28',
            '비영리 및 사회운동': '29'
        }
        
        self.country_mapping = {
            '한국': 'KR',
            '미국': 'US',
            '일본': 'JP',
            '중국': 'CN',
            '스페인': 'ES',
            '인도': 'IN',
            '유럽': 'GB',
            '동남아': 'TH'
        }
        
        self.duration_mapping = {
            '쇼츠': 'short',
            '중간 길이': 'medium',
            '긴 영상': 'long'
        }
        
        self.order_mapping = {
            '관련성': 'relevance',
            '조회수': 'viewCount',
            '업로드 날짜': 'date'
        }

    def _get_published_after(self, period: str) -> Optional[str]:
        now = datetime.now()
        if period == '7일 이내':
            date = now - timedelta(days=7)
        elif period == '1개월 이내':
            date = now - timedelta(days=30)
        elif period == '3개월 이내':
            date = now - timedelta(days=90)
        elif period == '6개월 이내':
            date = now - timedelta(days=180)
        elif period == '12개월 이내':
            date = now - timedelta(days=365)
        else:
            return None
        return date.isoformat() + 'Z'

    def _parse_duration(self, duration_str: str) -> int:
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    def search_videos(self, 
                     category: str = '전체',
                     keywords: Optional[List[str]] = None,
                     order: str = '관련성',
                     max_results: int = 25,
                     duration: Optional[str] = None,
                     period: Optional[str] = None,
                     country: str = '한국',
                     license_type: str = '전체',
                     min_views: int = 0) -> List[Dict]:
        try:
            query = ' '.join(keywords) if keywords else ''
            search_params = {
                'part': 'snippet',
                'type': 'video',
                'maxResults': min(max_results, 50),
                'order': self.order_mapping.get(order, 'relevance'),
                'regionCode': self.country_mapping.get(country, 'KR')
            }
            
            if query:
                search_params['q'] = query
            
            if category != '전체' and category in self.category_mapping:
                category_id = self.category_mapping[category]
                if category_id:
                    search_params['videoCategoryId'] = category_id
            
            if duration and duration in self.duration_mapping:
                search_params['videoDuration'] = self.duration_mapping[duration]
            
            if period:
                published_after = self._get_published_after(period)
                if published_after:
                    search_params['publishedAfter'] = published_after
            
            if license_type == '크리에이티브 커먼즈':
                search_params['videoLicense'] = 'creativeCommon'
            elif license_type == '표준 라이센스':
                search_params['videoLicense'] = 'youtube'
            
            search_response = self.youtube.search().list(**search_params).execute()
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            if not video_ids:
                return []
            
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            results = []
            video_order = {item['id']['videoId']: idx for idx, item in enumerate(search_response['items'])}
            
            for video in videos_response['items']:
                try:
                    view_count = int(video['statistics'].get('viewCount', 0))
                    if view_count < min_views:
                        continue
                    
                    duration_seconds = self._parse_duration(video['contentDetails']['duration'])
                    duration_formatted = self._format_duration(duration_seconds)
                    
                    video_data = {
                        'video_id': video['id'],
                        'title': video['snippet']['title'],
                        'channel': video['snippet']['channelTitle'],
                        'published_at': video['snippet']['publishedAt'],
                        'view_count': view_count,
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'duration': duration_formatted,
                        'duration_seconds': duration_seconds,
                        'description': video['snippet']['description'][:200] + '...',
                        'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                        'url': f"https://www.youtube.com/watch?v={video['id']}",
                        'search_order': video_order.get(video['id'], 999)
                    }
                    results.append(video_data)
                except (KeyError, ValueError):
                    continue
            
            if order == '조회수':
                results.sort(key=lambda x: x['view_count'], reverse=True)
            elif order == '업로드 날짜':
                results.sort(key=lambda x: x['published_at'], reverse=True)
            else:
                results.sort(key=lambda x: x['search_order'])
            
            for result in results:
                result.pop('search_order', None)
            
            return results
            
        except HttpError as e:
            print(f"YouTube API 오류: {e}")
            return []
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return []

    def _format_duration(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def get_trending_videos(self, country: str = '한국', max_results: int = 50) -> List[Dict]:
        try:
            region_code = self.country_mapping.get(country, 'KR')
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=min(max_results, 50)
            ).execute()
            
            results = []
            for video in response['items']:
                duration_seconds = self._parse_duration(video['contentDetails']['duration'])
                video_data = {
                    'video_id': video['id'],
                    'title': video['snippet']['title'],
                    'channel': video['snippet']['channelTitle'],
                    'published_at': video['snippet']['publishedAt'],
                    'view_count': int(video['statistics'].get('viewCount', 0)),
                    'like_count': int(video['statistics'].get('likeCount', 0)),
                    'comment_count': int(video['statistics'].get('commentCount', 0)),
                    'duration': self._format_duration(duration_seconds),
                    'duration_seconds': duration_seconds,
                    'description': video['snippet']['description'][:200] + '...',
                    'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                    'url': f"https://www.youtube.com/watch?v={video['id']}"
                }
                results.append(video_data)
            return results
        except HttpError as e:
            print(f"YouTube API 오류: {e}")
            return []