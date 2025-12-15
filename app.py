# app_final.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as tbs
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from youtube_analyzer import YouTubeTrendAnalyzer
from config_manager import ConfigManager
from PIL import Image, ImageTk
import sys
import threading
import webbrowser
import requests
import io

class YouTubeMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Maker")
        self.root.geometry("1400x800")
        self.root.configure(bg='#2b2b2b')
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager()
        
        # API 키 로드 또는 입력 받기
        self.api_key = self.config_manager.load_api_key()
        
        if not self.api_key:
            # API 키가 없으면 입력 받기
            self.api_key = self.show_api_key_dialog()
            if not self.api_key:
                messagebox.showerror("오류", "API 키가 필요합니다.\n프로그램을 종료합니다.")
                sys.exit(1)
            # 입력받은 API 키 저장
            self.config_manager.save_api_key(self.api_key)
        
        # YouTube Analyzer 초기화
        try:
            self.analyzer = YouTubeTrendAnalyzer(self.api_key)
        except ValueError as e:
            messagebox.showerror("오류", f"API 키가 올바르지 않습니다.\n{str(e)}")
            # 잘못된 API 키 삭제
            self.config_manager.clear_api_key()
            sys.exit(1)

        # 이미지 캐시
        self.image_cache = {}
        
        # 현재 활성 탭
        self.current_tab = "youtube_analysis"

        # GUI 구성
        self.create_widgets()

    def show_api_key_dialog(self):
        """API 키 입력 다이얼로그 표시"""
        dialog = tk.Toplevel(self.root)
        dialog.title("YouTube API 키 설정")
        dialog.geometry("800x600")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"800x600+{x}+{y}")
        
        api_key_result = [None]  # 결과 저장용
        
        # 메인 프레임
        main_frame = ttk.Frame(dialog, padding="30")
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 제목
        ttk.Label(main_frame,
                 text="🔑 YouTube API 키 설정",
                 font=('Helvetica', 16, 'bold'),
                 bootstyle="primary").pack(pady=(0, 10))
        
        # 설명
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=X, pady=(0, 20))
        
        desc_text = """YouTube Data API 키가 필요합니다.

API 키 발급 방법:
1. Google Cloud Console 접속 (console.cloud.google.com)
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리" 클릭
4. "YouTube Data API v3" 검색 및 활성화
5. "사용자 인증 정보" → "사용자 인증 정보 만들기" → "API 키" 선택
6. 생성된 API 키 복사

※ API 키는 안전하게 로컬에 저장됩니다."""
        
        ttk.Label(desc_frame,
                 text=desc_text,
                 font=('Helvetica', 9),
                 bootstyle="secondary",
                 justify=LEFT).pack(anchor=W)
        
        # 입력 프레임
        input_frame = ttk.LabelFrame(main_frame, text="API 키 입력", padding="15")
        input_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(input_frame,
                 text="API 키:",
                 font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(input_frame,
                                  textvariable=api_key_var,
                                  font=('Helvetica', 10),
                                  width=60)
        api_key_entry.pack(fill=X)
        api_key_entry.focus()
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        def on_ok():
            key = api_key_var.get().strip()
            if not key:
                messagebox.showwarning("경고", "API 키를 입력해주세요.", parent=dialog)
                return
            if len(key) < 20:
                messagebox.showwarning("경고", "올바른 API 키 형식이 아닙니다.", parent=dialog)
                return
            api_key_result[0] = key
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame,
                  text="✅ 확인",
                  command=on_ok,
                  bootstyle="primary",
                  width=15).pack(side=RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame,
                  text="❌ 취소",
                  command=on_cancel,
                  bootstyle="secondary",
                  width=15).pack(side=RIGHT)
        
        # Enter 키로 확인
        api_key_entry.bind('<Return>', lambda e: on_ok())
        
        # 다이얼로그가 닫힐 때까지 대기
        dialog.wait_window()
        
        return api_key_result[0]

    def create_widgets(self):
        # 메인 컨테이너
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES)
        
        # 좌우 분할
        main_container.columnconfigure(0, weight=0, minsize=200)  # 사이드바
        main_container.columnconfigure(1, weight=1)  # 콘텐츠
        main_container.rowconfigure(0, weight=1)

        # ========== 왼쪽 사이드바 ==========
        self.create_sidebar(main_container)
        
        # ========== 오른쪽 콘텐츠 영역 ==========
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.grid(row=0, column=1, sticky=(N, S, E, W))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # 초기 화면 - 유튜브 분석 탭 표시
        self.show_youtube_analysis()

    def create_sidebar(self, parent):
        """왼쪽 사이드바 생성"""
        sidebar = ttk.Frame(parent, bootstyle="dark")
        sidebar.grid(row=0, column=0, sticky=(N, S, E, W))
        
        # 로고/타이틀
        logo_frame = ttk.Frame(sidebar, bootstyle="dark")
        logo_frame.pack(fill=X, padx=15, pady=20)
        
        ttk.Label(logo_frame, 
                 text="🎬 콘텐츠 스튜디오", 
                 font=('Helvetica', 14, 'bold'),
                 bootstyle="inverse-dark").pack(anchor=W)
        
        # 구분선
        ttk.Separator(sidebar, orient='horizontal').pack(fill=X, padx=10, pady=10)
        
        # 메뉴 버튼들
        menu_frame = ttk.Frame(sidebar, bootstyle="dark")
        menu_frame.pack(fill=BOTH, expand=YES, padx=5)
        
        # 메뉴 아이템들
        menus = [
            ("📊 유튜브 분석", "youtube_analysis", "primary"),
            ("🎨 썸네일 생성", "thumbnail_maker", "secondary"),
            ("✍️ 제목/설명 생성", "title_generator", "secondary"),
            ("🎬 영상 제작", "video_maker", "secondary"),
            ("📈 채널 분석", "channel_analytics", "secondary"),
            ("⚙️ 설정", "settings", "secondary"),
        ]
        
        self.menu_buttons = {}
        for text, key, style in menus:
            btn = ttk.Button(menu_frame,
                           text=text,
                           command=lambda k=key: self.switch_tab(k),
                           bootstyle=f"{style}-outline",
                           width=20)
            btn.pack(fill=X, pady=3)
            self.menu_buttons[key] = btn
        
        # 활성 탭 표시
        self.menu_buttons["youtube_analysis"].configure(bootstyle="primary")
        
        # 하단 정보
        ttk.Separator(sidebar, orient='horizontal').pack(fill=X, padx=10, pady=10, side=BOTTOM)
        
        info_frame = ttk.Frame(sidebar, bootstyle="dark")
        info_frame.pack(side=BOTTOM, fill=X, padx=15, pady=10)
        
        ttk.Label(info_frame,
                 text="v1.0.0",
                 font=('Helvetica', 8),
                 bootstyle="inverse-secondary").pack(anchor=W)

    def switch_tab(self, tab_key):
        """탭 전환"""
        self.current_tab = tab_key
        
        # 모든 버튼 스타일 리셋
        for key, btn in self.menu_buttons.items():
            if key == tab_key:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="secondary-outline")
        
        # 콘텐츠 영역 클리어
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 해당 탭 표시
        if tab_key == "youtube_analysis":
            self.show_youtube_analysis()
        elif tab_key == "thumbnail_maker":
            self.show_coming_soon("썸네일 생성")
        elif tab_key == "title_generator":
            self.show_coming_soon("제목/설명 생성")
        elif tab_key == "video_maker":
            self.show_coming_soon("영상 제작")
        elif tab_key == "channel_analytics":
            self.show_coming_soon("채널 분석")
        elif tab_key == "settings":
            self.show_settings()

    def show_coming_soon(self, feature_name):
        """개발 예정 화면"""
        container = ttk.Frame(self.content_frame)
        container.pack(fill=BOTH, expand=YES)
        
        center_frame = ttk.Frame(container)
        center_frame.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        ttk.Label(center_frame,
                 text="🚧",
                 font=('Helvetica', 64)).pack()
        
        ttk.Label(center_frame,
                 text=f"{feature_name} 기능",
                 font=('Helvetica', 24, 'bold')).pack(pady=(20, 10))
        
        ttk.Label(center_frame,
                 text="곧 출시 예정입니다",
                 font=('Helvetica', 14),
                 bootstyle="secondary").pack()

    def show_settings(self):
        """설정 화면"""
        container = ttk.Frame(self.content_frame, padding="20")
        container.pack(fill=BOTH, expand=YES)
        
        # 헤더
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=X, pady=(0, 30))
        
        ttk.Label(header_frame,
                 text="⚙️ 설정",
                 font=('Helvetica', 20, 'bold'),
                 bootstyle="primary").pack(anchor=W)
        
        ttk.Label(header_frame,
                 text="애플리케이션 설정을 관리합니다",
                 font=('Helvetica', 10),
                 bootstyle="secondary").pack(anchor=W, pady=(5, 0))
        
        # API 키 설정 섹션
        api_section = ttk.LabelFrame(container, 
                                     text="🔑 API 키 관리",
                                     padding="20",
                                     bootstyle="primary")
        api_section.pack(fill=X, pady=(0, 20))
        
        # 현재 API 키 상태
        status_frame = ttk.Frame(api_section)
        status_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(status_frame,
                 text="현재 상태:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W, pady=5)
        
        if self.api_key:
            masked_key = self.api_key[:8] + "..." + self.api_key[-4:]
            status_text = f"✅ 설정됨 ({masked_key})"
            status_style = "success"
        else:
            status_text = "❌ 설정되지 않음"
            status_style = "danger"
        
        ttk.Label(status_frame,
                 text=status_text,
                 font=('Helvetica', 10),
                 bootstyle=status_style).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # 버튼들
        button_frame = ttk.Frame(api_section)
        button_frame.pack(fill=X)
        
        def change_api_key():
            """API 키 변경"""
            new_key = self.show_api_key_dialog()
            if new_key:
                # 새 API 키로 analyzer 재초기화
                try:
                    self.analyzer = YouTubeTrendAnalyzer(new_key)
                    self.api_key = new_key
                    self.config_manager.save_api_key(new_key)
                    messagebox.showinfo("성공", "API 키가 성공적으로 변경되었습니다.")
                    self.show_settings()  # 화면 새로고침
                except ValueError as e:
                    messagebox.showerror("오류", f"올바르지 않은 API 키입니다.\n{str(e)}")
        
        def test_api_key():
            """API 키 테스트"""
            try:
                # 간단한 API 호출로 테스트
                test_result = self.analyzer.youtube.videos().list(
                    part='snippet',
                    chart='mostPopular',
                    regionCode='KR',
                    maxResults=1
                ).execute()
                
                if test_result:
                    messagebox.showinfo("성공", "✅ API 키가 정상적으로 작동합니다!")
                else:
                    messagebox.showwarning("경고", "API 키는 유효하지만 응답이 없습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"❌ API 키 테스트 실패\n\n{str(e)}")
        
        def delete_api_key():
            """API 키 삭제"""
            if messagebox.askyesno("확인", 
                                  "저장된 API 키를 삭제하시겠습니까?\n다음 실행 시 다시 입력해야 합니다.",
                                  parent=container):
                self.config_manager.clear_api_key()
                messagebox.showinfo("완료", "API 키가 삭제되었습니다.")
                self.show_settings()  # 화면 새로고침
        
        ttk.Button(button_frame,
                  text="🔄 API 키 변경",
                  command=change_api_key,
                  bootstyle="primary",
                  width=20).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(button_frame,
                  text="🧪 연결 테스트",
                  command=test_api_key,
                  bootstyle="info",
                  width=20).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(button_frame,
                  text="🗑️ API 키 삭제",
                  command=delete_api_key,
                  bootstyle="danger",
                  width=20).pack(side=LEFT)
        
        # 도움말 섹션
        help_section = ttk.LabelFrame(container,
                                     text="💡 도움말",
                                     padding="20",
                                     bootstyle="info")
        help_section.pack(fill=X, pady=(0, 20))
        
        help_text = """API 키 발급 방법:

1. Google Cloud Console (console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리" 클릭
4. "YouTube Data API v3" 검색 및 활성화
5. "사용자 인증 정보" → "사용자 인증 정보 만들기" → "API 키" 선택
6. 생성된 API 키를 복사하여 위의 "API 키 변경" 버튼으로 입력

※ API 키는 암호화되어 로컬에만 저장됩니다.
※ 저장 위치: {}""".format(self.config_manager.config_file)
        
        ttk.Label(help_section,
                 text=help_text,
                 font=('Helvetica', 9),
                 bootstyle="secondary",
                 justify=LEFT).pack(anchor=W)
        
        # 정보 섹션
        info_section = ttk.LabelFrame(container,
                                     text="ℹ️ 애플리케이션 정보",
                                     padding="20",
                                     bootstyle="secondary")
        info_section.pack(fill=X)
        
        info_frame = ttk.Frame(info_section)
        info_frame.pack(fill=X)
        
        info_data = [
            ("버전", "1.0.0"),
            ("개발", "YouTube Maker Team"),
            ("설정 파일", str(self.config_manager.config_file)),
        ]
        
        for i, (label, value) in enumerate(info_data):
            ttk.Label(info_frame,
                     text=f"{label}:",
                     font=('Helvetica', 9, 'bold')).grid(row=i, column=0, sticky=W, pady=3)
            ttk.Label(info_frame,
                     text=value,
                     font=('Helvetica', 9)).grid(row=i, column=1, sticky=W, padx=(10, 0), pady=3)

    def show_youtube_analysis(self):
        """유튜브 분석 탭"""
        # 메인 컨테이너
        analysis_container = ttk.Frame(self.content_frame)
        analysis_container.pack(fill=BOTH, expand=YES)
        
        # 좌우 분할
        analysis_container.columnconfigure(0, weight=0, minsize=380)
        analysis_container.columnconfigure(1, weight=1)
        analysis_container.rowconfigure(0, weight=1)
        
        # ========== 왼쪽 필터 패널 ==========
        left_panel = ttk.Frame(analysis_container, padding="10")
        left_panel.grid(row=0, column=0, sticky=(N, S, E, W), padx=(10, 5))
        
        # 스크롤 가능한 왼쪽 패널
        left_scroll = ScrolledFrame(left_panel, autohide=True)
        left_scroll.pack(fill=BOTH, expand=YES)
        
        # 헤더
        header_frame = ttk.Frame(left_scroll)
        header_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(header_frame,
                 text="YouTube 트렌드 분석",
                 font=('Helvetica', 16, 'bold'),
                 bootstyle="primary").pack(anchor=W)
        
        ttk.Label(header_frame,
                 text="실시간 트렌드와 키워드 분석",
                 font=('Helvetica', 9),
                 bootstyle="secondary").pack(anchor=W, pady=(3, 0))
        
        # 필터 프레임
        filter_frame = ttk.LabelFrame(left_scroll,
                                     text="검색 설정",
                                     padding="15",
                                     bootstyle="primary")
        filter_frame.pack(fill=X, pady=(0, 10))
        
        # 검색 모드
        ttk.Label(filter_frame, text="검색 모드", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.mode_var = tk.StringVar(value="search")
        
        mode_frame = ttk.Frame(filter_frame)
        mode_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Radiobutton(mode_frame,
                       text="🔍 키워드 검색",
                       variable=self.mode_var,
                       value="search",
                       command=self.toggle_filters,
                       bootstyle="primary-toolbutton").pack(fill=X, pady=2)
        
        ttk.Radiobutton(mode_frame,
                       text="📈 인기 급상승",
                       variable=self.mode_var,
                       value="trending",
                       command=self.toggle_filters,
                       bootstyle="success-toolbutton").pack(fill=X, pady=2)
        
        # 국가
        ttk.Label(filter_frame, text="국가", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(5, 5))
        
        self.country_var = tk.StringVar(value="한국")
        countries = ["한국", "미국", "일본", "중국", "스페인", "인도", "유럽", "동남아"]
        ttk.Combobox(filter_frame,
                    textvariable=self.country_var,
                    values=countries,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 검색 필터들
        self.search_filters = ttk.Frame(filter_frame)
        self.search_filters.pack(fill=X, pady=(5, 0))
        
        # 카테고리
        ttk.Label(self.search_filters, text="카테고리", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.category_var = tk.StringVar(value="전체")
        categories = ["전체", "영화 및 애니메이션", "자동차 및 차량", "음악", "애완동물 및 동물",
                     "스포츠", "여행 및 이벤트", "게임", "인물 및 블로그", "코미디",
                     "엔터테인먼트", "뉴스 및 정치", "노하우 및 스타일", "교육", "과학 기술",
                     "비영리 및 사회운동"]
        
        ttk.Combobox(self.search_filters,
                    textvariable=self.category_var,
                    values=categories,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 키워드
        ttk.Label(self.search_filters, text="키워드", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.keywords_var = tk.StringVar()
        ttk.Entry(self.search_filters,
                 textvariable=self.keywords_var,
                 font=('Helvetica', 10)).pack(fill=X, pady=(0, 10))
        
        # 정렬 방식
        ttk.Label(self.search_filters, text="정렬 방식", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.order_var = tk.StringVar(value="관련성")
        orders = ["관련성", "조회수", "업로드 날짜"]
        ttk.Combobox(self.search_filters,
                    textvariable=self.order_var,
                    values=orders,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 최대 결과 수
        ttk.Label(self.search_filters, text="최대 결과 수", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.max_results_var = tk.StringVar(value="25")
        ttk.Entry(self.search_filters,
                 textvariable=self.max_results_var,
                 font=('Helvetica', 10)).pack(fill=X, pady=(0, 10))
        
        # 영상 길이
        ttk.Label(self.search_filters, text="영상 길이", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.duration_var = tk.StringVar(value="")
        durations = ["", "쇼츠", "중간 길이", "긴 영상"]
        ttk.Combobox(self.search_filters,
                    textvariable=self.duration_var,
                    values=durations,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 기간
        ttk.Label(self.search_filters, text="기간", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.period_var = tk.StringVar(value="")
        periods = ["", "7일 이내", "1개월 이내", "3개월 이내", "6개월 이내", "12개월 이내"]
        ttk.Combobox(self.search_filters,
                    textvariable=self.period_var,
                    values=periods,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 라이센스
        ttk.Label(self.search_filters, text="라이센스", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.license_var = tk.StringVar(value="전체")
        licenses = ["전체", "크리에이티브 커먼즈", "표준 라이센스"]
        ttk.Combobox(self.search_filters,
                    textvariable=self.license_var,
                    values=licenses,
                    state="readonly",
                    bootstyle="primary").pack(fill=X, pady=(0, 10))
        
        # 최소 조회수
        ttk.Label(self.search_filters, text="최소 조회수", font=('Helvetica', 10, 'bold')).pack(anchor=W, pady=(0, 5))
        
        self.min_views_var = tk.StringVar(value="0")
        ttk.Entry(self.search_filters,
                 textvariable=self.min_views_var,
                 font=('Helvetica', 10)).pack(fill=X, pady=(0, 10))
        
        # 검색 버튼
        ttk.Button(left_scroll,
                  text="🔍 검색 시작",
                  command=self.search,
                  bootstyle="primary",
                  width=30).pack(fill=X, pady=(10, 0))
        
        # ========== 오른쪽 결과 패널 ==========
        right_panel = ttk.Frame(analysis_container, padding="10")
        right_panel.grid(row=0, column=1, sticky=(N, S, E, W))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # 결과 프레임
        self.result_frame = ScrolledFrame(right_panel, autohide=True)
        self.result_frame.pack(fill=BOTH, expand=YES)
        
        # 초기 메시지
        welcome_frame = ttk.Frame(self.result_frame)
        welcome_frame.pack(expand=YES)
                
        ttk.Label(welcome_frame,
                 text="검색 조건을 설정하고\n검색 버튼을 눌러주세요",
                 font=('Helvetica', 14),
                 bootstyle="secondary",
                 justify=CENTER).pack(pady=20)
        
        # 초기 필터 표시
        self.toggle_filters()

    def toggle_filters(self):
        """필터 표시/숨김"""
        if self.mode_var.get() == "search":
            self.search_filters.pack(fill=X, pady=(5, 0))
        else:
            self.search_filters.pack_forget()

    def load_thumbnail(self, url):
        """썸네일 로드"""
        if url not in self.image_cache:
            try:
                response = requests.get(url, timeout=5)
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((180, 135), Image.Resampling.LANCZOS)
                self.image_cache[url] = ImageTk.PhotoImage(img)
            except Exception:
                self.image_cache[url] = None
        return self.image_cache[url]

    def create_video_card(self, parent, video, index):
        """비디오 카드 생성"""
        card_container = ttk.Frame(parent, bootstyle="light")
        card_container.grid(row=index, column=0, sticky=(W, E), pady=6, padx=8)
        parent.columnconfigure(0, weight=1)
        
        card = ttk.Frame(card_container, style='Card.TFrame', relief='raised', borderwidth=1)
        card.pack(fill=BOTH, expand=YES, padx=2, pady=2)
        card.columnconfigure(1, weight=1)
        
        # 썸네일
        thumbnail_frame = ttk.Frame(card)
        thumbnail_frame.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky=N)
        
        photo = self.load_thumbnail(video['thumbnail'])
        if photo:
            thumbnail_label = ttk.Label(thumbnail_frame, image=photo, cursor="hand2")
            thumbnail_label.image = photo
            thumbnail_label.pack()
            thumbnail_label.bind("<Button-1>", lambda e: webbrowser.open(video['url']))
        
        # 콘텐츠
        content_frame = ttk.Frame(card)
        content_frame.grid(row=0, column=1, sticky=(W, E, N), padx=(0, 10), pady=10)
        content_frame.columnconfigure(0, weight=1)
        
        # 제목
        title_label = ttk.Label(content_frame,
                               text=video['title'],
                               wraplength=600,
                               font=('Helvetica', 12, 'bold'),
                               cursor="hand2")
        title_label.grid(row=0, column=0, sticky=W, pady=(0, 6))
        title_label.bind("<Button-1>", lambda e: webbrowser.open(video['url']))
        
        # 채널
        ttk.Label(content_frame,
                 text=f"📺 {video['channel']}",
                 font=('Helvetica', 10),
                 bootstyle="info").grid(row=1, column=0, sticky=W, pady=(0, 6))
        
        # 통계
        stats_frame = ttk.Frame(content_frame)
        stats_frame.grid(row=2, column=0, sticky=W, pady=(0, 4))
        
        stats_text = f"👁 {video['view_count']:,}회  •  👍 {video['like_count']:,}  •  💬 {video['comment_count']:,}"
        ttk.Label(stats_frame,
                 text=stats_text,
                 font=('Helvetica', 9),
                 foreground='#666666').pack(side=LEFT)
        
        # 메타
        meta_text = f"⏱ {video['duration']}  •  📅 {video['published_at'][:10]}"
        ttk.Label(content_frame,
                 text=meta_text,
                 font=('Helvetica', 9),
                 foreground='#888888').grid(row=3, column=0, sticky=W)
        
        # 버튼
        button_frame = ttk.Frame(card)
        button_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=10)
        
        ttk.Button(button_frame,
                  text="▶️ 재생",
                  command=lambda: webbrowser.open(video['url']),
                  bootstyle="danger",
                  width=10).pack()

    def search(self):
        """검색 실행"""
        def run_search():
            # 기존 결과 삭제
            for widget in self.result_frame.winfo_children():
                widget.destroy()
            
            # 로딩
            loading = ttk.Label(self.result_frame,
                              text="🔄 검색 중...",
                              font=('Helvetica', 14),
                              bootstyle="info")
            loading.pack(pady=50)
            self.root.update()
            
            try:
                if self.mode_var.get() == "trending":
                    results = self.analyzer.get_trending_videos(
                        country=self.country_var.get(),
                        max_results=25
                    )
                    title = f"🔥 {self.country_var.get()} 인기 급상승 동영상"
                else:
                    keywords = self.keywords_var.get().strip().split() if self.keywords_var.get().strip() else None
                    max_results = int(self.max_results_var.get()) if self.max_results_var.get().isdigit() else 25
                    min_views = int(self.min_views_var.get()) if self.min_views_var.get().isdigit() else 0
                    
                    results = self.analyzer.search_videos(
                        category=self.category_var.get(),
                        keywords=keywords,
                        order=self.order_var.get(),
                        max_results=max_results,
                        duration=self.duration_var.get() or None,
                        period=self.period_var.get() or None,
                        country=self.country_var.get(),
                        license_type=self.license_var.get(),
                        min_views=min_views
                    )
                    
                    keyword_text = ', '.join(keywords) if keywords else '전체'
                    title = f"🔍 검색 결과: {keyword_text}"
                
                loading.destroy()
                
                # 헤더
                header_frame = ttk.Frame(self.result_frame)
                header_frame.grid(row=0, column=0, sticky=(W, E), pady=(5, 10), padx=8)
                
                ttk.Label(header_frame,
                         text=title,
                         font=('Helvetica', 16, 'bold'),
                         bootstyle="primary").pack(side=LEFT)
                
                ttk.Label(header_frame,
                         text=f"총 {len(results)}개",
                         font=('Helvetica', 12),
                         bootstyle="secondary").pack(side=LEFT, padx=(10, 0))
                
                # 결과
                if results:
                    for i, video in enumerate(results, 1):
                        self.create_video_card(self.result_frame, video, i)
                else:
                    no_result = ttk.Frame(self.result_frame)
                    no_result.grid(row=1, column=0, pady=50)
                    
                    ttk.Label(no_result,
                             text="😕",
                             font=('Helvetica', 24)).pack()
                    
                    ttk.Label(no_result,
                             text="검색 결과가 없습니다",
                             font=('Helvetica', 14)).pack(pady=10)
                    
            except Exception as e:
                loading.destroy()
                error_frame = ttk.Frame(self.result_frame)
                error_frame.pack(pady=50)
                
                ttk.Label(error_frame,
                         text="⚠️",
                         font=('Helvetica', 48)).pack()
                
                ttk.Label(error_frame,
                         text=f"오류 발생: {str(e)}",
                         font=('Helvetica', 12),
                         bootstyle="danger").pack(pady=10)
        
        threading.Thread(target=run_search, daemon=True).start()


if __name__ == "__main__":
    root = tbs.Window(themename="cosmo")
    app = YouTubeMakerApp(root)
    root.mainloop()