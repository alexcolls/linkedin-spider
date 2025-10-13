# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-12

### Added
- Initial release of LinkedIn Spider
- Interactive CLI with ASCII art and menu system
- Google Search integration for finding LinkedIn profiles
- Profile scraping with data extraction (name, title, company, location, about, followers)
- LinkedIn login integration with anti-detection features
- Export functionality (CSV, JSON, Excel)
- Configuration via environment variables (.env) and YAML (config.yaml)
- Optional VPN integration for IP rotation
- Progress bars and rich formatting for terminal output
- Auto-connect feature for sending connection requests
- Comprehensive logging system
- Profile data models with validation and deduplication
- Browser management with Selenium WebDriver
- Random delays and user agent rotation for anti-detection
- **Installation scripts** (install.sh, run.sh, uninstall.sh)
- System-wide installation option with global `linkedin-spider` command
- Development installation mode with Poetry
- Automatic dependency installation (Python, Poetry, Chrome/Chromium)
- Interactive installation wizard with multiple installation modes

### Features
- 🔍 Smart search via Google to avoid LinkedIn rate limits
- 🎨 Beautiful interactive CLI interface
- 📊 Multiple data export formats
- 🔐 Secure credential management
- 🌐 Optional VPN support
- ⚡ Progress tracking and batch processing
- 🛡️ Anti-detection measures
- 🚀 Easy installation with interactive wizard
- 🔧 System and development installation modes
- 🗑️ Clean uninstallation script

### Documentation
- Comprehensive README with installation and usage instructions
- Quick start guide with installation scripts
- Configuration examples and best practices
- Legal and ethical considerations
- Troubleshooting guide
- MIT License
- Contributing guidelines
- Detailed CHANGELOG

### Installation
- Three installation modes: system, development, or both
- Automatic dependency detection and installation
- Support for both Poetry and pip workflows
- Chrome/Chromium automatic setup
- Environment configuration wizard

## [0.1.1] - 2025-01-13

### Added
- 🤖 **CAPTCHA Detection**: Automatic detection of Google CAPTCHA challenges
- 🛑 **CAPTCHA Handler**: Interactive user-guided CAPTCHA resolution with pause/resume
- 📂 **Smart Data Directory**: Data folder now created in user's current working directory instead of installation path
- 🔄 **Environment Variable Preservation**: Wrapper script preserves user's working directory via `LINKEDIN_SPIDER_CWD`

### Fixed
- 🐛 Fixed CLI not running interactive menu by default when no command provided
- 🐛 Fixed data directory pointing to installation path instead of user's working directory
- 🐛 Fixed page iteration breaking when Google shows CAPTCHA
- 🐛 Fixed scraper continuing without results when CAPTCHA is present

### Changed
- 📝 Updated README with CAPTCHA handling and data directory explanations
- 🔧 Improved wrapper script to capture and preserve user context
- 🎯 Changed CLI callback to properly handle subcommands and default interactive mode

### Technical Details
- Added `_detect_captcha()` method with multiple detection strategies (iframes, selectors, keywords)
- Added `_wait_for_captcha_resolution()` method for user interaction
- Integrated CAPTCHA checks in `_scrape_current_page()` and `_go_to_next_page()` methods
- Modified `config.data_dir` property to use `LINKEDIN_SPIDER_CWD` environment variable
- Updated install.sh wrapper script to export user's working directory

[0.1.1]: https://github.com/alexcolls/linkedin-spider/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/alexcolls/linkedin-spider/releases/tag/v0.1.0
