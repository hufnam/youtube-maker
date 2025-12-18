# app_final.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import ttkbootstrap as tbs
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from youtube_analyzer import YouTubeTrendAnalyzer
from gemini_script_generator import GeminiScriptGenerator
from gemini_image_generator import GeminiImageGenerator
from music_image_generator import MusicImageGenerator
from config_manager import ConfigManager
from prompt_template_manager import PromptTemplateManager
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
        
        # API 키 로드 (선택적)
        self.api_key = self.config_manager.load_api_key()
        
        # YouTube Analyzer 초기화 (선택적)
        self.analyzer = None
        if self.api_key:
            try:
                self.analyzer = YouTubeTrendAnalyzer(self.api_key)
            except Exception as e:
                print(f"YouTube Analyzer 초기화 실패: {e}")
                # 잘못된 API 키는 삭제
                self.config_manager.clear_api_key()
                self.api_key = None
        
        # Gemini Script Generator 초기화 (선택적)
        self.gemini_generator = None
        self.gemini_image_generator = None
        self.music_image_generator = None
        gemini_key = self.config_manager.load_gemini_api_key()
        if gemini_key:
            try:
                self.gemini_generator = GeminiScriptGenerator(gemini_key)
                self.gemini_image_generator = GeminiImageGenerator(gemini_key)
                self.music_image_generator = MusicImageGenerator(gemini_key)
            except Exception as e:
                print(f"Gemini 초기화 실패: {e}")
                # Gemini는 선택적이므로 에러 무시

        self.template_manager = PromptTemplateManager()

        # 이미지 생성 관련 상태
        self.image_cuts_data = []  # 컷별 이미지 데이터 저장
        self.music_cuts_data = []  # 음악 이미지 컷별 데이터 저장

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
        dialog.geometry("1500x1000")  # 너비 700, 높이 500으로 증가
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (1500 // 2)  # 너비에 맞춰 중앙 계산
        y = (dialog.winfo_screenheight() // 2) - (1000 // 2)  # 높이에 맞춰 중앙 계산
        dialog.geometry(f"1500x1000+{x}+{y}")
        
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
    
    def show_gemini_api_key_dialog(self):
        """Gemini API 키 입력 다이얼로그 표시"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Gemini API 키 설정")
        dialog.geometry("1500x1000")  # 너비 700, 높이 500으로 증가
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (1500 // 2)  # 너비에 맞춰 중앙 계산
        y = (dialog.winfo_screenheight() // 2) - (1000 // 2)  # 높이에 맞춰 중앙 계산
        dialog.geometry(f"1500x1000+{x}+{y}")
        
        api_key_result = [None]  # 결과 저장용
        
        # 메인 프레임
        main_frame = ttk.Frame(dialog, padding="30")
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 제목
        ttk.Label(main_frame,
                 text="🤖 Gemini API 키 설정",
                 font=('Helvetica', 16, 'bold'),
                 bootstyle="success").pack(pady=(0, 10))
        
        # 설명
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=X, pady=(0, 20))
        
        desc_text = """대본 생성 기능을 사용하려면 Gemini API 키가 필요합니다.

【Gemini API 키 발급 방법】
1. Google AI Studio 접속 (aistudio.google.com)
2. Google 계정으로 로그인
3. 왼쪽 사이드바에서 "Get API Key" 클릭
4. "Create API key" 버튼 클릭
5. 생성된 API 키 복사

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
                 text="Gemini API 키:",
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
                  bootstyle="success",
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
            ("🔓 유튜브 분석", "youtube_analysis", "primary"),
            ("🗂️ 정보 수집", "data_collector", "secondary"),
            ("📝 대본 생성", "script_generator", "secondary"),
            ("🎞️ 이미지 생성", "image_maker", "secondary"),
            ("🎵 음악 이미지 생성", "music_image_maker", "secondary"),
            ("🎬 영상 스크립트 생성", "video_script_generator", "secondary"),
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
                 text="v1.0.1",
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
        elif tab_key == "data_collector":
            self.show_coming_soon("정보 수집")
        elif tab_key == "script_generator":
            self.show_script_generator()
        elif tab_key == "image_maker":
            self.show_image_maker()
        elif tab_key == "music_image_maker":
            self.show_music_image_maker()
        elif tab_key == "video_script_generator":
            self.show_coming_soon("영상 스크립트 생성")
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

    def show_script_generator(self):
        """대본 생성 화면 - 컷 스토리보드 기반"""
        # Gemini API 키 확인
        if not self.gemini_generator:
            self.show_gemini_setup_required()
            return
        
        container = ttk.Frame(self.content_frame, padding="20")
        container.pack(fill=BOTH, expand=YES)
        
        # 헤더
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(header_frame,
                 text="📝 YouTube 대본 생성 (컷 스토리보드)",
                 font=('Helvetica', 20, 'bold'),
                 bootstyle="primary").pack(anchor=W)
        
        ttk.Label(header_frame,
                 text="AI가 6-8초 단위의 컷으로 구성된 영상 대본을 생성합니다",
                 font=('Helvetica', 11),
                 bootstyle="secondary").pack(anchor=W, pady=(8, 0))
        
        # 메인 컨테이너 (3분할: 입력/결과/프롬프트)
        main_container = ttk.Frame(container)
        main_container.pack(fill=BOTH, expand=YES)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=2)
        main_container.columnconfigure(2, weight=1)
        
        # ===== 왼쪽: 입력 폼 =====
        input_frame = ttk.LabelFrame(main_container,
                                     text="📋 대본 설정",
                                     padding="10",
                                     bootstyle="info")
        input_frame.grid(row=0, column=0, sticky=(N, S, W, E), padx=(0, 5))
        
        # 주제
        ttk.Label(input_frame,
                 text="영상 주제 *",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        topic_entry = ttk.Entry(input_frame, font=('Helvetica', 11), width=35)
        topic_entry.pack(fill=X, pady=(0, 12))
        topic_entry.insert(0, "AI 영상 제작의 미래")
        
        # 대본 언어
        ttk.Label(input_frame,
                 text="대본 언어 *",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        language_var = tk.StringVar(value="한국어")
        language_frame = ttk.Frame(input_frame)
        language_frame.pack(fill=X, pady=(0, 12))
        
        ttk.Radiobutton(language_frame,
                       text="한국어",
                       variable=language_var,
                       value="한국어",
                       bootstyle="primary-toolbutton").pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(language_frame,
                       text="English",
                       variable=language_var,
                       value="영어",
                       bootstyle="primary-toolbutton").pack(side=LEFT)
        
        # 포맷
        ttk.Label(input_frame,
                 text="포맷 *",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        format_var = tk.StringVar(value="롱폼")
        format_frame = ttk.Frame(input_frame)
        format_frame.pack(fill=X, pady=(0, 12))
        
        ttk.Radiobutton(format_frame,
                       text="롱폼",
                       variable=format_var,
                       value="롱폼",
                       bootstyle="success-toolbutton").pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(format_frame,
                       text="숏폼",
                       variable=format_var,
                       value="숏폼",
                       bootstyle="success-toolbutton").pack(side=LEFT)
        
        # 영상 길이
        ttk.Label(input_frame,
                 text="영상 길이 (분) *",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        duration_frame = ttk.Frame(input_frame)
        duration_frame.pack(fill=X, pady=(0, 8))
        
        duration_var = tk.IntVar(value=1)
        duration_spinbox = ttk.Spinbox(duration_frame,
                                       from_=1,
                                       to=10,
                                       textvariable=duration_var,
                                       font=('Helvetica', 11),
                                       width=8)
        duration_spinbox.pack(side=LEFT)
        ttk.Label(duration_frame,
                 text="분",
                 font=('Helvetica', 11)).pack(side=LEFT, padx=(8, 0))
        
        # 컷 개수 표시
        cuts_label = ttk.Label(input_frame,
                               text="→ 약 10개 컷",
                               font=('Helvetica', 10),
                               bootstyle="secondary")
        cuts_label.pack(anchor=W, pady=(5, 12))
        
        def update_cuts_count(*args):
            cuts = duration_var.get() * 10
            cuts_label.config(text=f"→ 약 {cuts}개 컷")
        
        duration_var.trace('w', update_cuts_count)
        
        # 대상 시청자
        ttk.Label(input_frame,
                 text="대상 시청자",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        audience_entry = ttk.Entry(input_frame, font=('Helvetica', 11), width=35)
        audience_entry.pack(fill=X, pady=(0, 12))
        audience_entry.insert(0, "20-30대")
        
        # 템플릿 선택
        ttk.Label(input_frame,
                 text="프롬프트 템플릿",
                 font=('Helvetica', 11, 'bold')).pack(anchor=W, pady=(8, 5))
        
        template_var = tk.StringVar(value="default")
        template_combo = ttk.Combobox(input_frame,
                                     textvariable=template_var,
                                     font=('Helvetica', 10),
                                     width=32,
                                     state="readonly")
        template_combo['values'] = self.template_manager.get_template_names()
        template_combo.pack(fill=X, pady=(0, 15))
        
        # 생성 버튼
        generate_btn = ttk.Button(input_frame,
                                 text="✨ 대본 생성하기",
                                 command=lambda: self.generate_script_new(
                                     topic_entry.get(),
                                     language_var.get(),
                                     format_var.get(),
                                     duration_var.get(),
                                     audience_entry.get(),
                                     template_var.get(),
                                     result_text,
                                     prompt_text
                                 ),
                                 bootstyle="success",
                                 width=25)
        generate_btn.pack(pady=(10, 0))
        
        # ===== 중앙: 결과 표시 =====
        result_frame = ttk.LabelFrame(main_container,
                                      text="📄 생성된 대본",
                                      padding="10",
                                      bootstyle="primary")
        result_frame.grid(row=0, column=1, sticky=(N, S, W, E), padx=(5, 5))
        
        # 스크롤 가능한 텍스트 영역 - 줄 간격 추가
        result_text = scrolledtext.ScrolledText(result_frame,
                                                font=('Courier', 10),
                                                wrap=tk.WORD)
        result_text.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # 줄 간격 설정: spacing1(줄 위), spacing3(줄 아래)
        result_text.configure(spacing1=3, spacing2=3, spacing3=3)
        
        result_text.insert("1.0", """💡 대본 생성 안내

【컷 스토리보드 형식】
영상은 6-8초 단위의 컷으로 구성됩니다.
1분당 약 10개의 컷이 생성됩니다.

【포맷 선택】
• 롱폼: 자세한 설명, 스토리텔링
• 숏폼: 빠른 전개, 강렬한 훅

【생성 팁】
• 구체적인 주제를 입력하세요
• 원하는 포맷에 맞게 선택하세요
• 프롬프트 템플릿은 오른쪽에서 편집 가능합니다

왼쪽에서 설정을 입력하고 생성 버튼을 눌러주세요.""")
        result_text.config(state=tk.DISABLED)
        
        # 버튼 프레임
        button_frame = ttk.Frame(result_frame)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame,
                  text="📋 복사",
                  command=lambda: self.copy_to_clipboard(result_text),
                  bootstyle="info-outline",
                  width=15).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(button_frame,
                  text="💾 저장",
                  command=lambda: self.save_script(result_text),
                  bootstyle="success-outline",
                  width=15).pack(side=LEFT)
        
        # ===== 오른쪽: 프롬프트 편집 =====
        prompt_frame = ttk.LabelFrame(main_container,
                                      text="🎨 프롬프트 템플릿",
                                      padding="10",
                                      bootstyle="warning")
        prompt_frame.grid(row=0, column=2, sticky=(N, S, W, E), padx=(5, 0))
        
        # 프롬프트 텍스트 - 줄 간격 추가
        prompt_text = scrolledtext.ScrolledText(prompt_frame,
                                                font=('Courier', 10),
                                                wrap=tk.WORD)
        prompt_text.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # 줄 간격 설정
        prompt_text.configure(spacing1=3, spacing2=3, spacing3=3)
        
        # 기본 템플릿 로드
        default_template = self.template_manager.get_template("default")
        prompt_text.insert("1.0", default_template)
        
        # 템플릿 변경 시 업데이트
        def on_template_change(*args):
            selected = template_var.get()
            template = self.template_manager.get_template(selected)
            if template:
                prompt_text.delete("1.0", tk.END)
                prompt_text.insert("1.0", template)
        
        template_var.trace('w', on_template_change)
        
        # 프롬프트 버튼 프레임
        prompt_button_frame = ttk.Frame(prompt_frame)
        prompt_button_frame.pack(fill=X)
        
        def load_template_file():
            """템플릿 파일에서 불러오기"""
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="템플릿 불러오기",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template = f.read()
                    prompt_text.delete("1.0", tk.END)
                    prompt_text.insert("1.0", template)
                    messagebox.showinfo("성공", "템플릿을 불러왔습니다!")
                except Exception as e:
                    messagebox.showerror("오류", f"파일 읽기 실패:\n{str(e)}")
        
        def save_template_file():
            """현재 템플릿을 파일로 저장"""
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="템플릿 저장",
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
            )
            if file_path:
                try:
                    template = prompt_text.get("1.0", tk.END).strip()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(template)
                    messagebox.showinfo("성공", f"템플릿이 저장되었습니다:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("오류", f"파일 저장 실패:\n{str(e)}")
        
        def reset_template():
            """기본 템플릿으로 리셋"""
            if messagebox.askyesno("확인", "기본 템플릿으로 되돌리시겠습니까?"):
                self.template_manager.reset_to_default()
                template_combo['values'] = self.template_manager.get_template_names()
                template_var.set("default")
                on_template_change()
                messagebox.showinfo("완료", "기본 템플릿으로 리셋되었습니다.")
        
        # 3개 버튼 가로 배치
        ttk.Button(prompt_button_frame,
                  text="📁 불러오기",
                  command=load_template_file,
                  bootstyle="info-outline",
                  width=10).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(prompt_button_frame,
                  text="💾 파일저장",
                  command=save_template_file,
                  bootstyle="success-outline",
                  width=10).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(prompt_button_frame,
                  text="🔄 리셋",
                  command=reset_template,
                  bootstyle="secondary-outline",
                  width=10).pack(side=LEFT)
        
    def generate_script_new(self, topic, language, format_type, duration, audience, template_name, result_text, prompt_text):
        """새로운 대본 생성 실행 (컷 기반)"""
        if not topic:
            messagebox.showwarning("경고", "영상 주제를 입력해주세요.")
            return
        
        def run_generation():
            # 결과 텍스트 초기화
            result_text.config(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            result_text.insert("1.0", f"🔄 대본 생성 중...\n\n"
                                      f"잠시만 기다려주세요...")
            # spacing 재설정 (확실하게)
            result_text.configure(spacing1=3, spacing2=3, spacing3=3)
            result_text.config(state=tk.DISABLED)
            
            try:
                # 사용자 정의 프롬프트 사용
                custom_prompt = prompt_text.get("1.0", tk.END).strip()
                
                # 대본 생성
                script = self.gemini_generator.generate_script(
                    topic=topic,
                    language=language,
                    format_type=format_type,
                    duration=duration,
                    target_audience=audience,
                    custom_prompt=custom_prompt
                )
                
                # 결과 표시
                result_text.config(state=tk.NORMAL)
                result_text.delete("1.0", tk.END)
                if script:
                    result_text.insert("1.0", script)
                else:
                    result_text.insert("1.0", "❌ 대본 생성에 실패했습니다.\n다시 시도해주세요.")
                
                # spacing 재설정 (생성된 텍스트에도 적용)
                result_text.configure(spacing1=3, spacing2=3, spacing3=3)
                result_text.config(state=tk.DISABLED)
                
            except Exception as e:
                result_text.config(state=tk.NORMAL)
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", f"❌ 오류 발생:\n\n{str(e)}")
                # spacing 재설정
                result_text.configure(spacing1=3, spacing2=3, spacing3=3)
                result_text.config(state=tk.DISABLED)
        
        # 백그라운드에서 실행
        threading.Thread(target=run_generation, daemon=True).start()

    def show_youtube_setup_required(self):
        """YouTube API 키 설정 필요 안내"""
        container = ttk.Frame(self.content_frame)
        container.pack(fill=BOTH, expand=YES)
        
        center_frame = ttk.Frame(container)
        center_frame.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        ttk.Label(center_frame,
                 text="🔑",
                 font=('Helvetica', 64)).pack()
        
        ttk.Label(center_frame,
                 text="YouTube API 키가 필요합니다",
                 font=('Helvetica', 24, 'bold')).pack(pady=(20, 10))
        
        ttk.Label(center_frame,
                 text="YouTube 분석 기능을 사용하려면\nYouTube API 키를 설정해주세요",
                 font=('Helvetica', 12),
                 bootstyle="secondary",
                 justify=CENTER).pack(pady=(0, 20))
        
        ttk.Button(center_frame,
                  text="⚙️ 설정으로 이동",
                  command=lambda: self.switch_tab("settings"),
                  bootstyle="primary",
                  width=20).pack()

    def show_gemini_setup_required(self):
        """Gemini API 키 설정 필요 안내"""
        container = ttk.Frame(self.content_frame)
        container.pack(fill=BOTH, expand=YES)

        center_frame = ttk.Frame(container)
        center_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        ttk.Label(center_frame,
                 text="🤖",
                 font=('Helvetica', 64)).pack()

        ttk.Label(center_frame,
                 text="Gemini API 키가 필요합니다",
                 font=('Helvetica', 24, 'bold')).pack(pady=(20, 10))

        ttk.Label(center_frame,
                 text="이 기능을 사용하려면\nGemini API 키를 설정해주세요",
                 font=('Helvetica', 12),
                 bootstyle="secondary",
                 justify=CENTER).pack(pady=(0, 20))

        ttk.Button(center_frame,
                  text="⚙️ 설정으로 이동",
                  command=lambda: self.switch_tab("settings"),
                  bootstyle="success",
                  width=20).pack()

    def show_image_maker(self):
        """이미지 생성 화면"""
        # Gemini API 키 확인
        if not self.gemini_image_generator:
            self.show_gemini_setup_required()
            return

        # 메인 컨테이너
        container = ttk.Frame(self.content_frame, padding="15")
        container.pack(fill=BOTH, expand=YES)

        # 헤더
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(header_frame,
                 text="🎞️ 컷별 이미지 생성",
                 font=('Helvetica', 18, 'bold'),
                 bootstyle="primary").pack(anchor=W)

        ttk.Label(header_frame,
                 text="대본을 입력하면 각 컷에 맞는 이미지를 AI가 자동 생성합니다",
                 font=('Helvetica', 10),
                 bootstyle="secondary").pack(anchor=W, pady=(5, 0))

        # 스크롤 가능한 메인 컨테이너
        main_scroll = ScrolledFrame(container, autohide=True)
        main_scroll.pack(fill=BOTH, expand=YES)

        # ========== 기능 1: 설정 영역 ==========
        settings_frame = ttk.LabelFrame(main_scroll,
                                       text="⚙️ 이미지 생성 설정",
                                       padding="15",
                                       bootstyle="primary")
        settings_frame.pack(fill=X, pady=(0, 15))

        # 설정 그리드
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill=X)
        settings_grid.columnconfigure(1, weight=1)
        settings_grid.columnconfigure(3, weight=1)
        settings_grid.columnconfigure(5, weight=1)

        # 모델 선택
        ttk.Label(settings_grid,
                 text="모델:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W, padx=(0, 10), pady=5)

        self.image_model_var = tk.StringVar(value="gemini-2.5-flash-image")
        model_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.image_model_var,
                                   values=["gemini-2.5-flash-image", "gemini-3-pro-image-preview"],
                                   state="readonly",
                                   width=35)
        model_combo.grid(row=0, column=1, sticky=W, padx=(0, 20), pady=5)

        # 스타일 선택
        ttk.Label(settings_grid,
                 text="스타일:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=2, sticky=W, padx=(0, 10), pady=5)

        self.style_var = tk.StringVar(value="Animation")
        style_options = [
            "Realistic Photography",
            "Animation",
            "3D Pixar Style",
            "Cyberpunk/Futuristic",
            "Cinematic Movie Frame",
            "Oil Painting"
        ]
        style_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.style_var,
                                   values=style_options,
                                   state="readonly",
                                   width=22)
        style_combo.grid(row=0, column=3, sticky=W, padx=(0, 10), pady=5)

        # 이미지 비율 선택
        ttk.Label(settings_grid,
                 text="비율:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=4, sticky=W, padx=(10, 10), pady=5)

        self.aspect_ratio_var = tk.StringVar(value="16:9")
        ratio_frame = ttk.Frame(settings_grid)
        ratio_frame.grid(row=0, column=5, sticky=W, pady=5)

        ttk.Radiobutton(ratio_frame,
                       text="롱폼 (16:9)",
                       variable=self.aspect_ratio_var,
                       value="16:9",
                       bootstyle="warning-toolbutton").pack(side=LEFT, padx=(0, 5))

        ttk.Radiobutton(ratio_frame,
                       text="숏폼 (9:16)",
                       variable=self.aspect_ratio_var,
                       value="9:16",
                       bootstyle="warning-toolbutton").pack(side=LEFT)

        # 두 번째 줄: 분위기, 색감, 조명
        ttk.Label(settings_grid,
                 text="분위기:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=W, padx=(0, 10), pady=5)

        self.mood_var = tk.StringVar(value="Cinematic")
        mood_options = [
            "Cinematic",
            "Dreamy/Soft",
            "Dark/Moody",
            "Energetic/Bright",
            "Nostalgic/Retro",
            "Epic & Grand",
            "Minimalist"
        ]
        mood_combo = ttk.Combobox(settings_grid,
                                  textvariable=self.mood_var,
                                  values=mood_options,
                                  state="readonly",
                                  width=22)
        mood_combo.grid(row=1, column=1, sticky=W, padx=(0, 20), pady=5)

        ttk.Label(settings_grid,
                 text="색감:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=2, sticky=W, padx=(0, 10), pady=5)

        self.color_var = tk.StringVar(value="Vibrant & Colorful")
        color_options = [
            "Vibrant & Colorful",
            "Monochrome/B&W",
            "Pastel/Soft",
            "Warm Earthy Tones",
            "Cool Blue/Teal",
            "High Contrast/Bold",
            "Muted/Desaturated",
            "Vintage/Sepia"
        ]
        color_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.color_var,
                                   values=color_options,
                                   state="readonly",
                                   width=22)
        color_combo.grid(row=1, column=3, sticky=W, padx=(0, 10), pady=5)

        ttk.Label(settings_grid,
                 text="조명:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=4, sticky=W, padx=(0, 10), pady=5)

        self.lighting_var = tk.StringVar(value="Natural Sunlight")
        lighting_options = [
            "Golden Hour",
            "Neon/Night City",
            "Studio Softbox",
            "Natural Sunlight",
            "Dramatic Rim Light"
        ]
        lighting_combo = ttk.Combobox(settings_grid,
                                      textvariable=self.lighting_var,
                                      values=lighting_options,
                                      state="readonly",
                                      width=22)
        lighting_combo.grid(row=1, column=5, sticky=W, pady=5)

        # 세 번째 줄: 카메라
        ttk.Label(settings_grid,
                 text="카메라:",
                 font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky=W, padx=(0, 10), pady=5)

        self.camera_var = tk.StringVar(value="Wide Angle")
        camera_options = [
            "Close-up",
            "Wide Angle",
            "Low Angle (Heroic)",
            "Top Down (Flat Lay)",
            "Bokeh/Macro",
            "First-Person (POV)"
        ]
        camera_combo = ttk.Combobox(settings_grid,
                                    textvariable=self.camera_var,
                                    values=camera_options,
                                    state="readonly",
                                    width=22)
        camera_combo.grid(row=2, column=1, sticky=W, padx=(0, 20), pady=5)

        # 힌트 레이블
        ttk.Label(settings_grid,
                 text="💡 카메라 설정은 전반적인 영상 구성에 적용됩니다",
                 font=('Helvetica', 9),
                 bootstyle="secondary").grid(row=2, column=2, columnspan=4, sticky=W, pady=5)

        # ========== 기능 2: 대본 입력 영역 ==========
        script_frame = ttk.LabelFrame(main_scroll,
                                     text="📝 대본 입력 (복사/붙여넣기)",
                                     padding="15",
                                     bootstyle="info")
        script_frame.pack(fill=X, pady=(0, 15))

        # 대본 텍스트 입력
        self.image_script_text = scrolledtext.ScrolledText(script_frame,
                                                           font=('Courier', 10),
                                                           wrap=tk.WORD,
                                                           height=12)
        self.image_script_text.pack(fill=X, pady=(0, 10))
        self.image_script_text.configure(spacing1=2, spacing2=2, spacing3=2)

        # 안내 텍스트
        self.image_script_text.insert("1.0", """대본 생성 탭에서 생성된 대본을 여기에 붙여넣기 하세요.

형식 예시:
=== CUT 1 (0:00-0:08) ===
[장면 설명]
도시의 야경이 펼쳐진 빌딩 옥상, 주인공이 서있다

[대사/내레이션]
오늘 여러분께 놀라운 이야기를 들려드리겠습니다

[음악/효과음]
긴장감 있는 배경음악
---

위와 같은 컷 형식의 대본을 입력하시면 자동으로 파싱됩니다.""")

        # 버튼 프레임
        button_frame = ttk.Frame(script_frame)
        button_frame.pack(fill=X)

        ttk.Button(button_frame,
                  text="📂 파일 불러오기",
                  command=self.load_script_file,
                  bootstyle="info-outline",
                  width=15).pack(side=LEFT, padx=(0, 10))

        self.generate_images_btn = ttk.Button(button_frame,
                                              text="✨ 프롬프트/이미지 생성",
                                              command=self.start_image_generation,
                                              bootstyle="success",
                                              width=25)
        self.generate_images_btn.pack(side=LEFT, padx=(0, 10))

        ttk.Button(button_frame,
                  text="🗑️ 초기화",
                  command=self.clear_image_generation,
                  bootstyle="danger-outline",
                  width=15).pack(side=LEFT)

        # 진행 상태
        self.image_progress_var = tk.StringVar(value="")
        self.image_progress_label = ttk.Label(button_frame,
                                              textvariable=self.image_progress_var,
                                              font=('Helvetica', 10),
                                              bootstyle="info")
        self.image_progress_label.pack(side=LEFT, padx=(20, 0))

        # ========== 기능 3: 결과 표시 영역 ==========
        results_frame = ttk.LabelFrame(main_scroll,
                                      text="🖼️ 생성 결과 (컷별 이미지)",
                                      padding="15",
                                      bootstyle="success")
        results_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        # 전체 저장 버튼
        save_all_frame = ttk.Frame(results_frame)
        save_all_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(save_all_frame,
                  text="💾 전체 이미지 저장",
                  command=self.save_all_images,
                  bootstyle="success",
                  width=20).pack(side=LEFT)

        ttk.Label(save_all_frame,
                 text="생성된 모든 이미지를 한 번에 저장합니다",
                 font=('Helvetica', 9),
                 bootstyle="secondary").pack(side=LEFT, padx=(10, 0))

        # 결과 컨테이너 (스크롤 가능)
        self.image_results_container = ttk.Frame(results_frame)
        self.image_results_container.pack(fill=BOTH, expand=YES)

        # 초기 메시지
        self.image_initial_message = ttk.Label(self.image_results_container,
                                               text="대본을 입력하고 '프롬프트/이미지 생성' 버튼을 클릭하세요.\n생성된 이미지가 여기에 컷별로 표시됩니다.",
                                               font=('Helvetica', 11),
                                               bootstyle="secondary",
                                               justify=CENTER)
        self.image_initial_message.pack(pady=50)

    def start_image_generation(self):
        """이미지 생성 프로세스 시작"""
        script = self.image_script_text.get("1.0", tk.END).strip()

        if not script or script.startswith("대본 생성 탭에서"):
            messagebox.showwarning("경고", "대본을 입력해주세요.")
            return

        # 대본 파싱
        cuts = self.gemini_image_generator.parse_script_to_cuts(script)

        if not cuts:
            messagebox.showwarning("경고", "컷을 파싱할 수 없습니다.\n올바른 형식의 대본을 입력해주세요.")
            return

        # 버튼 비활성화
        self.generate_images_btn.config(state=tk.DISABLED)
        self.image_progress_var.set(f"총 {len(cuts)}개 컷 처리 중...")

        def run_generation():
            try:
                # 1단계: 프롬프트 생성
                self.image_progress_var.set("프롬프트 생성 중...")

                cuts_with_prompts = self.gemini_image_generator.generate_image_prompts(
                    cuts=cuts,
                    style=self.style_var.get(),
                    mood=self.mood_var.get(),
                    color=self.color_var.get(),
                    lighting=self.lighting_var.get(),
                    camera=self.camera_var.get()
                )

                # 2단계: 이미지 생성
                def update_progress(current, total, message):
                    self.image_progress_var.set(f"{message} ({current}/{total})")

                results = self.gemini_image_generator.generate_all_images(
                    cuts_with_prompts=cuts_with_prompts,
                    model=self.image_model_var.get(),
                    aspect_ratio=self.aspect_ratio_var.get(),
                    progress_callback=update_progress
                )

                # UI 업데이트
                self.root.after(0, lambda: self.display_image_results(results))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"이미지 생성 실패:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self.generate_images_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.image_progress_var.set(""))

        threading.Thread(target=run_generation, daemon=True).start()

    def display_image_results(self, results):
        """이미지 생성 결과 표시"""
        # 기존 내용 삭제
        for widget in self.image_results_container.winfo_children():
            widget.destroy()

        self.image_cuts_data = results

        if not results:
            ttk.Label(self.image_results_container,
                     text="생성된 결과가 없습니다.",
                     font=('Helvetica', 11),
                     bootstyle="warning").pack(pady=50)
            return

        # 각 컷별 결과 표시
        for i, cut in enumerate(results):
            self.create_cut_result_card(self.image_results_container, cut, i)

    def create_cut_result_card(self, parent, cut, index):
        """개별 컷 결과 카드 생성"""
        # 카드 프레임
        card = ttk.LabelFrame(parent,
                             text=f"CUT {cut['cut_number']} ({cut['time_range']})",
                             padding="10",
                             bootstyle="info")
        card.pack(fill=X, pady=(0, 15))

        # 3분할 레이아웃: 대본 | 프롬프트 | 이미지
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=X)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.columnconfigure(2, weight=0)

        # 왼쪽: 대본 정보
        script_frame = ttk.Frame(content_frame)
        script_frame.grid(row=0, column=0, sticky=(N, S, W, E), padx=(0, 10))

        ttk.Label(script_frame,
                 text="📝 대본",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="primary").pack(anchor=W)

        script_text = scrolledtext.ScrolledText(script_frame,
                                                font=('Helvetica', 10),
                                                wrap=tk.WORD,
                                                height=12,
                                                width=35)
        script_text.pack(fill=X, pady=(5, 0))
        script_text.insert("1.0", f"[장면]\n{cut['scene_description']}\n\n[대사]\n{cut['narration']}")
        script_text.config(state=tk.DISABLED)
        script_text.configure(spacing1=3, spacing2=3, spacing3=3)

        # 중앙: 프롬프트 (편집 가능)
        prompt_frame = ttk.Frame(content_frame)
        prompt_frame.grid(row=0, column=1, sticky=(N, S, W, E), padx=(0, 10))

        ttk.Label(prompt_frame,
                 text="🎨 이미지 프롬프트 (편집 가능)",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="success").pack(anchor=W)

        prompt_text = scrolledtext.ScrolledText(prompt_frame,
                                                font=('Helvetica', 10),
                                                wrap=tk.WORD,
                                                height=12,
                                                width=40)
        prompt_text.pack(fill=X, pady=(5, 5))
        prompt_text.configure(spacing1=3, spacing2=3, spacing3=3)
        prompt_text.insert("1.0", cut.get('image_prompt', '프롬프트 생성 실패'))

        # 재생성 버튼
        regen_btn = ttk.Button(prompt_frame,
                              text="🔄 이미지 재생성",
                              command=lambda idx=index, pt=prompt_text: self.regenerate_single_image(idx, pt),
                              bootstyle="warning-outline",
                              width=18)
        regen_btn.pack(anchor=W)

        # 오른쪽: 이미지
        image_frame = ttk.Frame(content_frame)
        image_frame.grid(row=0, column=2, sticky=(N, S, W, E))

        ttk.Label(image_frame,
                 text="🖼️ 생성 이미지",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="info").pack(anchor=W)

        # 이미지 표시 영역
        image_display = ttk.Label(image_frame, text="")
        image_display.pack(pady=(5, 5))

        if cut.get('generated_image'):
            # PIL Image를 PhotoImage로 변환
            img = cut['generated_image']
            # 썸네일 크기로 리사이즈
            img_display = img.copy()
            img_display.thumbnail((256, 256), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_display)
            image_display.config(image=photo)
            image_display.image = photo  # 참조 유지

            # 이미지 인덱스 저장 (저장시 사용)
            image_display.cut_index = index
        elif cut.get('image_error'):
            image_display.config(text=f"❌ {cut['image_error'][:50]}...",
                               font=('Helvetica', 9),
                               bootstyle="danger")
        else:
            image_display.config(text="이미지 없음",
                               font=('Helvetica', 10),
                               bootstyle="secondary")

        # 개별 저장 버튼
        ttk.Button(image_frame,
                  text="💾 저장",
                  command=lambda idx=index: self.save_single_image(idx),
                  bootstyle="success-outline",
                  width=10).pack(anchor=W)

    def regenerate_single_image(self, cut_index, prompt_text_widget):
        """단일 컷 이미지 재생성"""
        new_prompt = prompt_text_widget.get("1.0", tk.END).strip()

        if not new_prompt:
            messagebox.showwarning("경고", "프롬프트를 입력해주세요.")
            return

        self.image_progress_var.set(f"컷 {cut_index + 1} 이미지 재생성 중...")

        def run_regeneration():
            try:
                cut = self.image_cuts_data[cut_index]
                updated_cut = self.gemini_image_generator.regenerate_cut_image(
                    cut=cut,
                    new_prompt=new_prompt,
                    model=self.image_model_var.get(),
                    aspect_ratio=self.aspect_ratio_var.get()
                )

                self.image_cuts_data[cut_index] = updated_cut

                # UI 업데이트
                self.root.after(0, lambda: self.display_image_results(self.image_cuts_data))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"재생성 실패:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self.image_progress_var.set(""))

        threading.Thread(target=run_regeneration, daemon=True).start()

    def save_single_image(self, cut_index):
        """단일 이미지 저장"""
        from tkinter import filedialog

        if cut_index >= len(self.image_cuts_data):
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        cut = self.image_cuts_data[cut_index]
        if not cut.get('generated_image'):
            messagebox.showwarning("경고", "이 컷에는 생성된 이미지가 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 파일", "*.png"), ("JPEG 파일", "*.jpg"), ("모든 파일", "*.*")],
            initialfile=f"cut_{cut['cut_number']}.png"
        )

        if file_path:
            try:
                cut['generated_image'].save(file_path)
                messagebox.showinfo("완료", f"이미지가 저장되었습니다:\n{file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")

    def save_all_images(self):
        """모든 이미지 일괄 저장"""
        from tkinter import filedialog

        if not self.image_cuts_data:
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        # 저장할 이미지가 있는지 확인
        images_to_save = [cut for cut in self.image_cuts_data if cut.get('generated_image')]

        if not images_to_save:
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        # 폴더 선택
        folder_path = filedialog.askdirectory(title="이미지 저장 폴더 선택")

        if folder_path:
            try:
                import os
                saved_count = 0

                for cut in images_to_save:
                    file_path = os.path.join(folder_path, f"cut_{cut['cut_number']:02d}.png")
                    cut['generated_image'].save(file_path)
                    saved_count += 1

                messagebox.showinfo("완료", f"{saved_count}개 이미지가 저장되었습니다:\n{folder_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")

    def load_script_file(self):
        """대본 텍스트 파일 불러오기"""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="대본 파일 선택",
            filetypes=[
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()

                # 기존 내용 지우고 새 내용 삽입
                self.image_script_text.delete("1.0", tk.END)
                self.image_script_text.insert("1.0", script_content)

                messagebox.showinfo("완료", f"파일을 불러왔습니다:\n{file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"파일을 불러오는데 실패했습니다:\n{str(e)}")

    def clear_image_generation(self):
        """이미지 생성 초기화"""
        # 텍스트 초기화
        self.image_script_text.delete("1.0", tk.END)
        self.image_script_text.insert("1.0", """대본 생성 탭에서 생성된 대본을 여기에 붙여넣기 하세요.

형식 예시:
=== CUT 1 (0:00-0:08) ===
[장면 설명]
도시의 야경이 펼쳐진 빌딩 옥상, 주인공이 서있다

[대사/내레이션]
오늘 여러분께 놀라운 이야기를 들려드리겠습니다

[음악/효과음]
긴장감 있는 배경음악
---

위와 같은 컷 형식의 대본을 입력하시면 자동으로 파싱됩니다.""")

        # 결과 영역 초기화
        for widget in self.image_results_container.winfo_children():
            widget.destroy()

        self.image_initial_message = ttk.Label(self.image_results_container,
                                               text="대본을 입력하고 '프롬프트/이미지 생성' 버튼을 클릭하세요.\n생성된 이미지가 여기에 컷별로 표시됩니다.",
                                               font=('Helvetica', 11),
                                               bootstyle="secondary",
                                               justify=CENTER)
        self.image_initial_message.pack(pady=50)

        # 데이터 초기화
        self.image_cuts_data = []
        self.image_progress_var.set("")

    def show_music_image_maker(self):
        """음악 이미지 생성 화면"""
        # Gemini API 키 확인
        if not self.music_image_generator:
            self.show_gemini_setup_required()
            return

        # 메인 컨테이너
        container = ttk.Frame(self.content_frame, padding="15")
        container.pack(fill=BOTH, expand=YES)

        # 헤더
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(header_frame,
                 text="🎵 음악 이미지 생성",
                 font=('Helvetica', 18, 'bold'),
                 bootstyle="primary").pack(anchor=W)

        ttk.Label(header_frame,
                 text="가사를 입력하면 각 줄에 맞는 이미지를 AI가 자동 생성합니다",
                 font=('Helvetica', 10),
                 bootstyle="secondary").pack(anchor=W, pady=(5, 0))

        # 스크롤 가능한 메인 컨테이너
        main_scroll = ScrolledFrame(container, autohide=True)
        main_scroll.pack(fill=BOTH, expand=YES)

        # ========== 기능 1: 곡 정보 및 컨셉 ==========
        music_info_frame = ttk.LabelFrame(main_scroll,
                                          text="🎶 곡 정보 및 컨셉",
                                          padding="15",
                                          bootstyle="info")
        music_info_frame.pack(fill=X, pady=(0, 15))

        # 곡 정보 그리드
        info_grid = ttk.Frame(music_info_frame)
        info_grid.pack(fill=X)
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)

        # 곡 제목
        ttk.Label(info_grid,
                 text="곡 제목:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W, padx=(0, 10), pady=5)

        self.music_title_var = tk.StringVar()
        title_entry = ttk.Entry(info_grid,
                               textvariable=self.music_title_var,
                               font=('Helvetica', 10),
                               width=40)
        title_entry.grid(row=0, column=1, sticky=W, padx=(0, 20), pady=5)
        title_entry.insert(0, "예: Dynamite")

        # 비주얼 컨셉/테마
        ttk.Label(info_grid,
                 text="비주얼 컨셉/테마:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=W, padx=(0, 10), pady=5)

        self.music_concept_var = tk.StringVar()
        concept_entry = ttk.Entry(info_grid,
                                 textvariable=self.music_concept_var,
                                 font=('Helvetica', 10),
                                 width=80)
        concept_entry.grid(row=1, column=1, columnspan=3, sticky=W, pady=5)
        concept_entry.insert(0, "예: 비오는 사이버펑크 도시에서 추격전, 노을 지는 해변가에서 피아노 연주, 우주를 유영하는 고래")

        # 가사 입력
        lyrics_frame = ttk.Frame(music_info_frame)
        lyrics_frame.pack(fill=X, pady=(10, 0))

        ttk.Label(lyrics_frame,
                 text="가사:",
                 font=('Helvetica', 10, 'bold')).pack(anchor=W)

        ttk.Label(lyrics_frame,
                 text="줄바꿈을 기준으로 컷 이미지를 생성합니다.",
                 font=('Helvetica', 9),
                 bootstyle="secondary").pack(anchor=W, pady=(0, 5))

        self.music_lyrics_text = scrolledtext.ScrolledText(lyrics_frame,
                                                           font=('Helvetica', 10),
                                                           wrap=tk.WORD,
                                                           height=8)
        self.music_lyrics_text.pack(fill=X, pady=(0, 10))
        self.music_lyrics_text.configure(spacing1=2, spacing2=2, spacing3=2)
        self.music_lyrics_text.insert("1.0", "여기에 가사를 입력하세요.\n각 줄마다 하나의 이미지가 생성됩니다.\n빈 줄은 무시됩니다.")

        # 장르, 템포, 곡 무드 선택
        options_frame = ttk.Frame(music_info_frame)
        options_frame.pack(fill=X, pady=(10, 0))

        # 장르 선택
        genre_frame = ttk.LabelFrame(options_frame, text="장르", padding="5")
        genre_frame.pack(side=LEFT, padx=(0, 15))

        self.music_genre_var = tk.StringVar(value="Pop")
        genre_options = ["Pop", "K-Pop", "Jazz/Blues", "Folk", "R&B", "Hip-Hop",
                        "Rock/Alternative", "EDM", "Classical/Orchestral", "Ambient/Chill"]

        genre_combo = ttk.Combobox(genre_frame,
                                   textvariable=self.music_genre_var,
                                   values=genre_options,
                                   state="readonly",
                                   width=18)
        genre_combo.pack()

        # 템포 선택
        tempo_frame = ttk.LabelFrame(options_frame, text="템포", padding="5")
        tempo_frame.pack(side=LEFT, padx=(0, 15))

        self.music_tempo_var = tk.StringVar(value="Moderate")
        tempo_options = ["Slow", "Moderate", "Fast", "Intense"]

        tempo_btn_frame = ttk.Frame(tempo_frame)
        tempo_btn_frame.pack()
        for tempo in tempo_options:
            ttk.Radiobutton(tempo_btn_frame,
                           text=tempo,
                           variable=self.music_tempo_var,
                           value=tempo,
                           bootstyle="info-toolbutton").pack(side=LEFT, padx=2)

        # 곡 무드 선택
        mood_frame = ttk.LabelFrame(options_frame, text="곡 무드", padding="5")
        mood_frame.pack(side=LEFT)

        self.music_mood_var = tk.StringVar(value="Euphoric/Uplifting")
        music_mood_options = ["Euphoric/Uplifting", "Melancholic/Emotional", "Dreamy/Ethereal",
                             "Dark/Intense", "Calm/Peaceful", "Romantic/Sentimental", "Mysterious/Enigmatic"]

        music_mood_combo = ttk.Combobox(mood_frame,
                                        textvariable=self.music_mood_var,
                                        values=music_mood_options,
                                        state="readonly",
                                        width=22)
        music_mood_combo.pack()

        # ========== 기능 2: 이미지 생성 설정 ==========
        settings_frame = ttk.LabelFrame(main_scroll,
                                       text="⚙️ 이미지 생성 설정",
                                       padding="15",
                                       bootstyle="primary")
        settings_frame.pack(fill=X, pady=(0, 15))

        # 설정 그리드
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill=X)
        settings_grid.columnconfigure(1, weight=1)
        settings_grid.columnconfigure(3, weight=1)
        settings_grid.columnconfigure(5, weight=1)

        # 모델 선택
        ttk.Label(settings_grid,
                 text="모델:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W, padx=(0, 10), pady=5)

        self.music_image_model_var = tk.StringVar(value="gemini-2.5-flash-image")
        model_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.music_image_model_var,
                                   values=["gemini-2.5-flash-image", "gemini-3-pro-image-preview"],
                                   state="readonly",
                                   width=35)
        model_combo.grid(row=0, column=1, sticky=W, padx=(0, 20), pady=5)

        # 스타일 선택
        ttk.Label(settings_grid,
                 text="스타일:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=2, sticky=W, padx=(0, 10), pady=5)

        self.music_style_var = tk.StringVar(value="Animation")
        style_options = [
            "Realistic Photography",
            "Animation",
            "3D Pixar Style",
            "Cyberpunk/Futuristic",
            "Cinematic Movie Frame",
            "Oil Painting"
        ]
        style_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.music_style_var,
                                   values=style_options,
                                   state="readonly",
                                   width=22)
        style_combo.grid(row=0, column=3, sticky=W, padx=(0, 10), pady=5)

        # 이미지 비율 선택
        ttk.Label(settings_grid,
                 text="비율:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=4, sticky=W, padx=(10, 10), pady=5)

        self.music_aspect_ratio_var = tk.StringVar(value="16:9")
        ratio_frame = ttk.Frame(settings_grid)
        ratio_frame.grid(row=0, column=5, sticky=W, pady=5)

        ttk.Radiobutton(ratio_frame,
                       text="롱폼 (16:9)",
                       variable=self.music_aspect_ratio_var,
                       value="16:9",
                       bootstyle="warning-toolbutton").pack(side=LEFT, padx=(0, 5))

        ttk.Radiobutton(ratio_frame,
                       text="숏폼 (9:16)",
                       variable=self.music_aspect_ratio_var,
                       value="9:16",
                       bootstyle="warning-toolbutton").pack(side=LEFT)

        # 두 번째 줄: 분위기, 색감, 조명
        ttk.Label(settings_grid,
                 text="분위기:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=W, padx=(0, 10), pady=5)

        self.music_visual_mood_var = tk.StringVar(value="Cinematic")
        visual_mood_options = [
            "Cinematic",
            "Dreamy/Soft",
            "Dark/Moody",
            "Energetic/Bright",
            "Nostalgic/Retro",
            "Epic & Grand",
            "Minimalist"
        ]
        mood_combo = ttk.Combobox(settings_grid,
                                  textvariable=self.music_visual_mood_var,
                                  values=visual_mood_options,
                                  state="readonly",
                                  width=22)
        mood_combo.grid(row=1, column=1, sticky=W, padx=(0, 20), pady=5)

        ttk.Label(settings_grid,
                 text="색감:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=2, sticky=W, padx=(0, 10), pady=5)

        self.music_color_var = tk.StringVar(value="Vibrant & Colorful")
        color_options = [
            "Vibrant & Colorful",
            "Monochrome/B&W",
            "Pastel/Soft",
            "Warm Earthy Tones",
            "Cool Blue/Teal",
            "High Contrast/Bold",
            "Muted/Desaturated",
            "Vintage/Sepia"
        ]
        color_combo = ttk.Combobox(settings_grid,
                                   textvariable=self.music_color_var,
                                   values=color_options,
                                   state="readonly",
                                   width=22)
        color_combo.grid(row=1, column=3, sticky=W, padx=(0, 10), pady=5)

        ttk.Label(settings_grid,
                 text="조명:",
                 font=('Helvetica', 10, 'bold')).grid(row=1, column=4, sticky=W, padx=(0, 10), pady=5)

        self.music_lighting_var = tk.StringVar(value="Natural Sunlight")
        lighting_options = [
            "Golden Hour",
            "Neon/Night City",
            "Studio Softbox",
            "Natural Sunlight",
            "Dramatic Rim Light"
        ]
        lighting_combo = ttk.Combobox(settings_grid,
                                      textvariable=self.music_lighting_var,
                                      values=lighting_options,
                                      state="readonly",
                                      width=22)
        lighting_combo.grid(row=1, column=5, sticky=W, pady=5)

        # 세 번째 줄: 카메라
        ttk.Label(settings_grid,
                 text="카메라:",
                 font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky=W, padx=(0, 10), pady=5)

        self.music_camera_var = tk.StringVar(value="Wide Angle")
        camera_options = [
            "Close-up",
            "Wide Angle",
            "Low Angle (Heroic)",
            "Top Down (Flat Lay)",
            "Bokeh/Macro",
            "First-Person (POV)"
        ]
        camera_combo = ttk.Combobox(settings_grid,
                                    textvariable=self.music_camera_var,
                                    values=camera_options,
                                    state="readonly",
                                    width=22)
        camera_combo.grid(row=2, column=1, sticky=W, padx=(0, 20), pady=5)

        # 힌트 레이블
        ttk.Label(settings_grid,
                 text="💡 카메라 설정은 전반적인 영상 구성에 적용됩니다",
                 font=('Helvetica', 9),
                 bootstyle="secondary").grid(row=2, column=2, columnspan=4, sticky=W, pady=5)

        # 버튼 프레임
        button_frame = ttk.Frame(main_scroll)
        button_frame.pack(fill=X, pady=(0, 15))

        self.music_generate_btn = ttk.Button(button_frame,
                                              text="✨ 이미지 생성",
                                              command=self.start_music_image_generation,
                                              bootstyle="success",
                                              width=25)
        self.music_generate_btn.pack(side=LEFT, padx=(0, 10))

        ttk.Button(button_frame,
                  text="🗑️ 초기화",
                  command=self.clear_music_image_generation,
                  bootstyle="danger-outline",
                  width=15).pack(side=LEFT)

        # 진행 상태
        self.music_progress_var = tk.StringVar(value="")
        self.music_progress_label = ttk.Label(button_frame,
                                              textvariable=self.music_progress_var,
                                              font=('Helvetica', 10),
                                              bootstyle="info")
        self.music_progress_label.pack(side=LEFT, padx=(20, 0))

        # ========== 기능 3: 결과 표시 영역 ==========
        results_frame = ttk.LabelFrame(main_scroll,
                                      text="🖼️ 생성 결과 (컷별 이미지)",
                                      padding="15",
                                      bootstyle="success")
        results_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        # 전체 저장 버튼
        save_all_frame = ttk.Frame(results_frame)
        save_all_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(save_all_frame,
                  text="💾 전체 이미지 저장",
                  command=self.save_all_music_images,
                  bootstyle="success",
                  width=20).pack(side=LEFT)

        ttk.Label(save_all_frame,
                 text="생성된 모든 이미지를 한 번에 저장합니다",
                 font=('Helvetica', 9),
                 bootstyle="secondary").pack(side=LEFT, padx=(10, 0))

        # 결과 컨테이너 (스크롤 가능)
        self.music_results_container = ttk.Frame(results_frame)
        self.music_results_container.pack(fill=BOTH, expand=YES)

        # 초기 메시지
        self.music_initial_message = ttk.Label(self.music_results_container,
                                               text="가사를 입력하고 '이미지 생성' 버튼을 클릭하세요.\n생성된 이미지가 여기에 컷별로 표시됩니다.",
                                               font=('Helvetica', 11),
                                               bootstyle="secondary",
                                               justify=CENTER)
        self.music_initial_message.pack(pady=50)

        # 음악 이미지 데이터 초기화
        self.music_cuts_data = []

    def start_music_image_generation(self):
        """음악 이미지 생성 프로세스 시작"""
        lyrics = self.music_lyrics_text.get("1.0", tk.END).strip()

        if not lyrics or lyrics.startswith("여기에 가사를"):
            messagebox.showwarning("경고", "가사를 입력해주세요.")
            return

        # 가사를 줄 단위로 파싱 (빈 줄 제외)
        lyrics_lines = [line.strip() for line in lyrics.split('\n') if line.strip()]

        if not lyrics_lines:
            messagebox.showwarning("경고", "유효한 가사가 없습니다.")
            return

        # 곡 정보 수집
        song_title = self.music_title_var.get().strip()
        if song_title.startswith("예:"):
            song_title = ""

        visual_concept = self.music_concept_var.get().strip()
        if visual_concept.startswith("예:"):
            visual_concept = ""

        genre = self.music_genre_var.get()
        tempo = self.music_tempo_var.get()
        music_mood = self.music_mood_var.get()

        # 버튼 비활성화
        self.music_generate_btn.config(state=tk.DISABLED)
        self.music_progress_var.set(f"총 {len(lyrics_lines)}개 컷 처리 중...")

        def run_generation():
            try:
                results = []
                total = len(lyrics_lines)

                for i, lyric_line in enumerate(lyrics_lines):
                    self.music_progress_var.set(f"컷 {i+1}/{total} 프롬프트 생성 중...")

                    # 프롬프트 생성
                    image_prompt = self.generate_music_image_prompt(
                        lyric_line=lyric_line,
                        song_title=song_title,
                        visual_concept=visual_concept,
                        genre=genre,
                        tempo=tempo,
                        music_mood=music_mood,
                        style=self.music_style_var.get(),
                        visual_mood=self.music_visual_mood_var.get(),
                        color=self.music_color_var.get(),
                        lighting=self.music_lighting_var.get(),
                        camera=self.music_camera_var.get()
                    )

                    self.music_progress_var.set(f"컷 {i+1}/{total} 이미지 생성 중...")

                    # 이미지 생성
                    image, error = self.gemini_image_generator.generate_single_image(
                        prompt=image_prompt,
                        model=self.music_image_model_var.get(),
                        aspect_ratio=self.music_aspect_ratio_var.get()
                    )

                    results.append({
                        'cut_number': i + 1,
                        'lyrics': lyric_line,
                        'image_prompt': image_prompt,
                        'generated_image': image,
                        'image_error': error
                    })

                    # API 호출 간 딜레이
                    if i < total - 1:
                        import time
                        time.sleep(1)

                # UI 업데이트
                self.root.after(0, lambda: self.display_music_image_results(results))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"이미지 생성 실패:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self.music_generate_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.music_progress_var.set(""))

        threading.Thread(target=run_generation, daemon=True).start()

    def generate_music_image_prompt(self, lyric_line, song_title, visual_concept, genre, tempo,
                                    music_mood, style, visual_mood, color, lighting, camera):
        """음악 이미지 생성을 위한 프롬프트 생성"""
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

        # 템포 설명 매핑
        tempo_descriptions = {
            "Slow": "slow, gentle movement, peaceful pace",
            "Moderate": "moderate tempo, balanced rhythm",
            "Fast": "fast paced, dynamic movement, energetic",
            "Intense": "intense, powerful, dramatic action"
        }

        # 음악 무드 설명 매핑
        music_mood_descriptions = {
            "Euphoric/Uplifting": "euphoric, uplifting, joyful atmosphere",
            "Melancholic/Emotional": "melancholic, emotional, touching, bittersweet",
            "Dreamy/Ethereal": "dreamy, ethereal, floating, surreal",
            "Dark/Intense": "dark, intense, dramatic, powerful",
            "Calm/Peaceful": "calm, peaceful, serene, tranquil",
            "Romantic/Sentimental": "romantic, sentimental, warm, intimate",
            "Mysterious/Enigmatic": "mysterious, enigmatic, intriguing, atmospheric"
        }

        style_keyword = style_descriptions.get(style, style)
        color_keyword = color_descriptions.get(color, color)
        tempo_keyword = tempo_descriptions.get(tempo, tempo)
        mood_keyword = music_mood_descriptions.get(music_mood, music_mood)

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

【Output Format】
Return ONLY the image generation prompt, nothing else. No quotes, no labels, just the prompt text."""

        try:
            response = self.gemini_image_generator.text_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            # 기본 프롬프트 반환
            return f"{style_keyword}, {lyric_line}, {mood_keyword}, {color_keyword}, {lighting} lighting, {camera} shot"

    def display_music_image_results(self, results):
        """음악 이미지 생성 결과 표시"""
        # 기존 내용 삭제
        for widget in self.music_results_container.winfo_children():
            widget.destroy()

        self.music_cuts_data = results

        if not results:
            ttk.Label(self.music_results_container,
                     text="생성된 결과가 없습니다.",
                     font=('Helvetica', 11),
                     bootstyle="warning").pack(pady=50)
            return

        # 각 컷별 결과 표시
        for i, cut in enumerate(results):
            self.create_music_cut_result_card(self.music_results_container, cut, i)

    def create_music_cut_result_card(self, parent, cut, index):
        """개별 음악 컷 결과 카드 생성"""
        # 카드 프레임
        card = ttk.LabelFrame(parent,
                             text=f"CUT {cut['cut_number']}",
                             padding="10",
                             bootstyle="info")
        card.pack(fill=X, pady=(0, 15))

        # 3분할 레이아웃: 가사 | 프롬프트 | 이미지
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=X)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.columnconfigure(2, weight=0)

        # 왼쪽: 가사 정보
        lyrics_frame = ttk.Frame(content_frame)
        lyrics_frame.grid(row=0, column=0, sticky=(N, S, W, E), padx=(0, 10))

        ttk.Label(lyrics_frame,
                 text="🎵 가사",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="primary").pack(anchor=W)

        lyrics_text = scrolledtext.ScrolledText(lyrics_frame,
                                                font=('Helvetica', 10),
                                                wrap=tk.WORD,
                                                height=12,
                                                width=35)
        lyrics_text.pack(fill=X, pady=(5, 0))
        lyrics_text.insert("1.0", cut['lyrics'])
        lyrics_text.config(state=tk.DISABLED)
        lyrics_text.configure(spacing1=3, spacing2=3, spacing3=3)

        # 중앙: 프롬프트 (편집 가능)
        prompt_frame = ttk.Frame(content_frame)
        prompt_frame.grid(row=0, column=1, sticky=(N, S, W, E), padx=(0, 10))

        ttk.Label(prompt_frame,
                 text="🎨 이미지 프롬프트 (편집 가능)",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="success").pack(anchor=W)

        prompt_text = scrolledtext.ScrolledText(prompt_frame,
                                                font=('Helvetica', 10),
                                                wrap=tk.WORD,
                                                height=12,
                                                width=40)
        prompt_text.pack(fill=X, pady=(5, 5))
        prompt_text.configure(spacing1=3, spacing2=3, spacing3=3)
        prompt_text.insert("1.0", cut.get('image_prompt', '프롬프트 생성 실패'))

        # 재생성 버튼
        regen_btn = ttk.Button(prompt_frame,
                              text="🔄 이미지 재생성",
                              command=lambda idx=index, pt=prompt_text: self.regenerate_single_music_image(idx, pt),
                              bootstyle="warning-outline",
                              width=18)
        regen_btn.pack(anchor=W)

        # 오른쪽: 이미지
        image_frame = ttk.Frame(content_frame)
        image_frame.grid(row=0, column=2, sticky=(N, S, W, E))

        ttk.Label(image_frame,
                 text="🖼️ 생성 이미지",
                 font=('Helvetica', 10, 'bold'),
                 bootstyle="info").pack(anchor=W)

        # 이미지 표시 영역
        image_display = ttk.Label(image_frame, text="")
        image_display.pack(pady=(5, 5))

        if cut.get('generated_image'):
            # PIL Image를 PhotoImage로 변환
            img = cut['generated_image']
            # 썸네일 크기로 리사이즈
            img_display = img.copy()
            img_display.thumbnail((256, 256), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_display)
            image_display.config(image=photo)
            image_display.image = photo  # 참조 유지

            # 이미지 인덱스 저장 (저장시 사용)
            image_display.cut_index = index
        elif cut.get('image_error'):
            image_display.config(text=f"❌ {cut['image_error'][:50]}...",
                               font=('Helvetica', 9),
                               bootstyle="danger")
        else:
            image_display.config(text="이미지 없음",
                               font=('Helvetica', 10),
                               bootstyle="secondary")

        # 개별 저장 버튼
        ttk.Button(image_frame,
                  text="💾 저장",
                  command=lambda idx=index: self.save_single_music_image(idx),
                  bootstyle="success-outline",
                  width=10).pack(anchor=W)

    def regenerate_single_music_image(self, cut_index, prompt_text_widget):
        """단일 음악 컷 이미지 재생성"""
        new_prompt = prompt_text_widget.get("1.0", tk.END).strip()

        if not new_prompt:
            messagebox.showwarning("경고", "프롬프트를 입력해주세요.")
            return

        self.music_progress_var.set(f"컷 {cut_index + 1} 이미지 재생성 중...")

        def run_regeneration():
            try:
                cut = self.music_cuts_data[cut_index]

                image, error = self.gemini_image_generator.generate_single_image(
                    prompt=new_prompt,
                    model=self.music_image_model_var.get(),
                    aspect_ratio=self.music_aspect_ratio_var.get()
                )

                cut['image_prompt'] = new_prompt
                cut['generated_image'] = image
                cut['image_error'] = error
                self.music_cuts_data[cut_index] = cut

                # UI 업데이트
                self.root.after(0, lambda: self.display_music_image_results(self.music_cuts_data))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"재생성 실패:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self.music_progress_var.set(""))

        threading.Thread(target=run_regeneration, daemon=True).start()

    def save_single_music_image(self, cut_index):
        """단일 음악 이미지 저장"""
        from tkinter import filedialog

        if cut_index >= len(self.music_cuts_data):
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        cut = self.music_cuts_data[cut_index]
        if not cut.get('generated_image'):
            messagebox.showwarning("경고", "이 컷에는 생성된 이미지가 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 파일", "*.png"), ("JPEG 파일", "*.jpg"), ("모든 파일", "*.*")],
            initialfile=f"music_cut_{cut['cut_number']}.png"
        )

        if file_path:
            try:
                cut['generated_image'].save(file_path)
                messagebox.showinfo("완료", f"이미지가 저장되었습니다:\n{file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")

    def save_all_music_images(self):
        """모든 음악 이미지 일괄 저장"""
        from tkinter import filedialog

        if not self.music_cuts_data:
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        # 저장할 이미지가 있는지 확인
        images_to_save = [cut for cut in self.music_cuts_data if cut.get('generated_image')]

        if not images_to_save:
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return

        # 폴더 선택
        folder_path = filedialog.askdirectory(title="이미지 저장 폴더 선택")

        if folder_path:
            try:
                import os
                saved_count = 0

                for cut in images_to_save:
                    file_path = os.path.join(folder_path, f"music_cut_{cut['cut_number']:02d}.png")
                    cut['generated_image'].save(file_path)
                    saved_count += 1

                messagebox.showinfo("완료", f"{saved_count}개 이미지가 저장되었습니다:\n{folder_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")

    def clear_music_image_generation(self):
        """음악 이미지 생성 초기화"""
        # 텍스트 초기화
        self.music_lyrics_text.delete("1.0", tk.END)
        self.music_lyrics_text.insert("1.0", "여기에 가사를 입력하세요.\n각 줄마다 하나의 이미지가 생성됩니다.\n빈 줄은 무시됩니다.")

        # 곡 정보 초기화
        self.music_title_var.set("예: Dynamite")
        self.music_concept_var.set("예: 비오는 사이버펑크 도시에서 추격전, 노을 지는 해변가에서 피아노 연주, 우주를 유영하는 고래")
        self.music_genre_var.set("Pop")
        self.music_tempo_var.set("Moderate")
        self.music_mood_var.set("Euphoric/Uplifting")

        # 결과 영역 초기화
        for widget in self.music_results_container.winfo_children():
            widget.destroy()

        self.music_initial_message = ttk.Label(self.music_results_container,
                                               text="가사를 입력하고 '이미지 생성' 버튼을 클릭하세요.\n생성된 이미지가 여기에 컷별로 표시됩니다.",
                                               font=('Helvetica', 11),
                                               bootstyle="secondary",
                                               justify=CENTER)
        self.music_initial_message.pack(pady=50)

        # 데이터 초기화
        self.music_cuts_data = []
        self.music_progress_var.set("")

    def generate_script(self, topic, duration, tone, audience, additional, result_text):
        """대본 생성 실행"""
        if not topic:
            messagebox.showwarning("경고", "영상 주제를 입력해주세요.")
            return
        
        def run_generation():
            # 결과 텍스트 초기화
            result_text.config(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            result_text.insert("1.0", "🔄 대본 생성 중...\n\n잠시만 기다려주세요...")
            result_text.config(state=tk.DISABLED)
            
            try:
                # 대본 생성
                script = self.gemini_generator.generate_script(
                    topic=topic,
                    duration=duration,
                    tone=tone,
                    target_audience=audience,
                    additional_requirements=additional
                )
                
                # 결과 표시
                result_text.config(state=tk.NORMAL)
                result_text.delete("1.0", tk.END)
                if script:
                    result_text.insert("1.0", script)
                else:
                    result_text.insert("1.0", "❌ 대본 생성에 실패했습니다.\n다시 시도해주세요.")
                result_text.config(state=tk.DISABLED)
                
            except Exception as e:
                result_text.config(state=tk.NORMAL)
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", f"❌ 오류 발생:\n\n{str(e)}\n\n"
                                         f"API 요청 한도를 초과했을 수 있습니다.\n"
                                         f"잠시 후 다시 시도해주세요.")
                result_text.config(state=tk.DISABLED)
        
        # 백그라운드에서 실행
        threading.Thread(target=run_generation, daemon=True).start()
    
    def copy_to_clipboard(self, text_widget):
        """클립보드에 복사"""
        text = text_widget.get("1.0", tk.END).strip()
        if text and not text.startswith("대본 설정을"):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("완료", "클립보드에 복사되었습니다!")
        else:
            messagebox.showwarning("경고", "복사할 내용이 없습니다.")
    
    def save_script(self, text_widget):
        """대본 파일로 저장"""
        from tkinter import filedialog
        text = text_widget.get("1.0", tk.END).strip()
        
        if not text or text.startswith("대본 설정을"):
            messagebox.showwarning("경고", "저장할 내용이 없습니다.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("완료", f"대본이 저장되었습니다:\n{file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")


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
        
        # YouTube API 키 설정 섹션
        youtube_api_section = ttk.LabelFrame(container, 
                                     text="🔑 YouTube API 키 관리",
                                     padding="20",
                                     bootstyle="primary")
        youtube_api_section.pack(fill=X, pady=(0, 20))
        
        # 현재 YouTube API 키 상태
        status_frame = ttk.Frame(youtube_api_section)
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
        button_frame = ttk.Frame(youtube_api_section)
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
            if not self.analyzer:
                messagebox.showwarning("경고", "YouTube API 키가 설정되지 않았습니다.")
                return
            
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
                                  "저장된 YouTube API 키를 삭제하시겠습니까?\nYouTube 분석 기능을 사용할 수 없습니다.",
                                  parent=container):
                self.config_manager.clear_api_key()
                self.api_key = None
                self.analyzer = None
                messagebox.showinfo("완료", "YouTube API 키가 삭제되었습니다.")
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
        
        # Gemini API 키 설정 섹션
        gemini_api_section = ttk.LabelFrame(container,
                                            text="🤖 Gemini API 키 관리 (대본 생성용)",
                                            padding="20",
                                            bootstyle="success")
        gemini_api_section.pack(fill=X, pady=(0, 20))
        
        # Gemini API 키 상태
        gemini_status_frame = ttk.Frame(gemini_api_section)
        gemini_status_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(gemini_status_frame,
                 text="현재 상태:",
                 font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W, pady=5)
        
        gemini_key = self.config_manager.load_gemini_api_key()
        if gemini_key:
            masked_gemini_key = gemini_key[:8] + "..." + gemini_key[-4:]
            gemini_status_text = f"✅ 설정됨 ({masked_gemini_key})"
            gemini_status_style = "success"
        else:
            gemini_status_text = "❌ 설정되지 않음 (대본 생성 불가)"
            gemini_status_style = "danger"
        
        ttk.Label(gemini_status_frame,
                 text=gemini_status_text,
                 font=('Helvetica', 10),
                 bootstyle=gemini_status_style).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Gemini 버튼들
        gemini_button_frame = ttk.Frame(gemini_api_section)
        gemini_button_frame.pack(fill=X)
        
        def change_gemini_key():
            """Gemini API 키 변경"""
            new_key = self.show_gemini_api_key_dialog()
            if new_key:
                try:
                    # 새 Gemini API 키로 generator 재초기화
                    self.gemini_generator = GeminiScriptGenerator(new_key)
                    self.config_manager.save_gemini_api_key(new_key)
                    messagebox.showinfo("성공", "Gemini API 키가 성공적으로 변경되었습니다.")
                    self.show_settings()  # 화면 새로고침
                except Exception as e:
                    messagebox.showerror("오류", f"올바르지 않은 Gemini API 키입니다.\n{str(e)}")
        
        def test_gemini_key():
            """Gemini API 키 테스트"""
            if not self.gemini_generator:
                messagebox.showwarning("경고", "Gemini API 키가 설정되지 않았습니다.")
                return
            
            try:
                # 간단한 생성 테스트
                response = self.gemini_generator.model.generate_content("Hello")
                if response:
                    messagebox.showinfo("성공", "✅ Gemini API 키가 정상적으로 작동합니다!")
                else:
                    messagebox.showwarning("경고", "응답을 받지 못했습니다.")
            except Exception as e:
                error_msg = str(e)
                messagebox.showerror("오류", f"❌ Gemini API 키 테스트 실패\n\n{error_msg}")
        
        def delete_gemini_key():
            """Gemini API 키 삭제"""
            if messagebox.askyesno("확인",
                                  "저장된 Gemini API 키를 삭제하시겠습니까?\n대본 생성 기능을 사용할 수 없습니다.",
                                  parent=container):
                self.config_manager.clear_gemini_api_key()
                self.gemini_generator = None
                messagebox.showinfo("완료", "Gemini API 키가 삭제되었습니다.")
                self.show_settings()  # 화면 새로고침
        
        ttk.Button(gemini_button_frame,
                  text="🔄 Gemini 키 변경",
                  command=change_gemini_key,
                  bootstyle="success",
                  width=20).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(gemini_button_frame,
                  text="🧪 연결 테스트",
                  command=test_gemini_key,
                  bootstyle="info",
                  width=20).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(gemini_button_frame,
                  text="🗑️ Gemini 키 삭제",
                  command=delete_gemini_key,
                  bootstyle="danger",
                  width=20).pack(side=LEFT)
        
        # 도움말 섹션
        help_section = ttk.LabelFrame(container,
                                     text="💡 도움말",
                                     padding="20",
                                     bootstyle="info")
        help_section.pack(fill=X, pady=(0, 20))
        
        help_text = """【YouTube API 키 발급】
1. Google Cloud Console (console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리" 클릭
4. "YouTube Data API v3" 검색 및 활성화
5. "사용자 인증 정보" → "사용자 인증 정보 만들기" → "API 키" 선택
6. 생성된 API 키를 복사하여 위의 "YouTube 키 변경" 버튼으로 입력

【Gemini API 키 발급】
1. Google AI Studio (aistudio.google.com) 접속
2. Google 계정으로 로그인
3. 왼쪽 사이드바에서 "Get API Key" 클릭
4. "Create API key" 버튼 클릭
5. 생성된 API 키를 복사하여 위의 "Gemini 키 변경" 버튼으로 입력

※ 모든 API 키는 암호화되어 로컬에만 저장됩니다.
※ 저장 위치: {}""".format(self.config_manager.config_file)
        
        ttk.Label(help_section,
                 text=help_text,
                 font=('Helvetica', 9),
                 bootstyle="secondary",
                 justify=LEFT).pack(anchor=W)
        
    def show_youtube_analysis(self):
        """유튜브 분석 탭"""
        # YouTube API 키 확인
        if not self.analyzer:
            self.show_youtube_setup_required()
            return
        
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
                              text="검색 중...",
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