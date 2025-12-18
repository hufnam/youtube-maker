# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Maker is a Korean-language desktop application for YouTube content creators. It provides:
- YouTube trend analysis (via YouTube Data API v3)
- AI-powered script generation (via Google Gemini API)
- Cut-based storyboard format for video scripts (6-8 second cuts)

## Running the Application

```bash
python app.py
```

## Dependencies

Install with:
```bash
pip install -r requirements.txt
```

Key dependencies: ttkbootstrap (GUI), google-api-python-client (YouTube API), google-generativeai (Gemini API), Pillow (images), pandas (data processing)

## Architecture

### Core Modules

- **app.py** - Main GUI application using ttkbootstrap. Contains `YouTubeMakerApp` class with sidebar navigation and tabbed content areas (YouTube analysis, script generator, settings).

- **youtube_analyzer.py** - `YouTubeTrendAnalyzer` class wraps YouTube Data API v3. Handles video search with filters (category, duration, period, license, min views) and trending video retrieval. Contains Korean-to-API mappings for categories, countries, and durations.

- **gemini_script_generator.py** - `GeminiScriptGenerator` class uses Gemini 2.5 Flash model. Generates cut-based storyboard scripts with retry logic for rate limits. Supports custom prompt templates with placeholders: `{topic}`, `{language}`, `{format_type}`, `{duration}`, `{total_cuts}`, `{target_audience}`.

- **config_manager.py** - `ConfigManager` handles API key persistence in `~/.youtube_maker/config.json`. Keys are base64 encoded. Manages both YouTube and Gemini API keys separately.

- **prompt_template_manager.py** - `PromptTemplateManager` stores prompt templates in `~/.youtube_maker/prompt_templates.json`. Supports custom template creation and reset to defaults.

### Data Flow

1. User configures API keys via Settings tab (stored in ~/.youtube_maker/)
2. YouTube analysis: User sets filters -> YouTubeTrendAnalyzer queries API -> Results displayed as video cards
3. Script generation: User inputs topic/settings -> Template filled with parameters -> Gemini generates cut-based storyboard

### GUI Structure

The app uses a sidebar navigation pattern:
- Left sidebar: Menu buttons for tab switching
- Right content area: Dynamic content based on selected tab
- Tabs: YouTube Analysis, Script Generator, Settings (others show "Coming Soon")

## API Keys

Both YouTube Data API v3 and Gemini API keys are required for full functionality. Keys are stored base64-encoded in `~/.youtube_maker/config.json`.
