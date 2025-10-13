# 🕷️ LinkedIn Spider

<div align="center">

![LinkedIn Spider](https://img.shields.io/badge/LinkedIn-Spider-blue?style=for-the-badge&logo=linkedin)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Manager-blue?style=for-the-badge&logo=poetry)](https://python-poetry.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**A professional CLI tool for scraping LinkedIn profiles via Google Search**

</div>

---

## 📖 Overview

LinkedIn Spider is a powerful, user-friendly command-line tool that helps you collect and analyze LinkedIn profiles at scale. By leveraging Google Search instead of direct LinkedIn scraping, it significantly reduces the risk of account restrictions while providing comprehensive profile data.

## ✨ Features

- 🔍 **Smart Search** - Find profiles via Google Search to avoid LinkedIn rate limits
- 🎨 **Beautiful CLI** - Interactive menu with ASCII art and rich formatting
- 📊 **Data Export** - Export to CSV, JSON, or Excel formats
- 🔐 **Secure** - Environment-based configuration for credentials
- 🌐 **VPN Support** - Optional IP rotation for enhanced privacy
- ⚡ **Fast & Efficient** - Progress tracking and batch processing
- 🛡️ **Anti-Detection** - Random delays, user agents, and human-like behavior
- 🤖 **CAPTCHA Handler** - Automatic CAPTCHA detection with user-guided resolution

## 📦 Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/alexcolls/linkedin-spider.git
cd linkedin-spider

# Run the installation script
./install.sh
```

The installation script provides three options:
1. **System Installation** - Installs globally as `linkedin-spider` command
2. **Development Installation** - Installs locally with Poetry for testing
3. **Both** - Installs both system and development modes

### Manual Installation

```bash
# Install dependencies with Poetry
poetry install

# Optional: Install with Excel support
poetry install -E excel

# Activate the virtual environment
poetry shell
```

## ⚙️ Configuration

### 1. Environment Variables

```bash
cp .env.sample .env
# Edit .env with your LinkedIn credentials
```

### 2. Configuration File

Edit `config.yaml` for advanced settings (delays, VPN, export format, etc.)

## 🎯 Usage

### Quick Start

```bash
# If installed with system mode
linkedin-spider

# If installed with development mode
./run.sh

# Or with Poetry directly
poetry run python -m linkedin_spider
```

### Interactive Mode

The CLI provides an interactive menu with ASCII art:
```bash
linkedin-spider  # or ./run.sh
```

Menu options:
1. 🔍 Search & Collect Profile URLs
2. 📊 Scrape Profile Data
3. 🤝 Auto-Connect to Profiles
4. 📁 View/Export Results
5. ⚙️ Configure Settings
6. ❓ Help
0. 🚪 Exit

### Command-Line Mode

```bash
# Search for profiles
linkedin-spider search "Python Developer" "San Francisco" --max-pages 10

# Scrape profiles from file
linkedin-spider scrape --urls data/profile_urls.txt --output results --format csv

# Show version
linkedin-spider version
```

## 🗑️ Uninstallation

To remove LinkedIn Spider from your system:

```bash
./uninstall.sh
```

This will:
- Remove the system command (if installed)
- Clean up Poetry virtual environments
- Optionally remove .env and data files

## 🔧 Key Features Explained

### CAPTCHA Handling

LinkedIn Spider automatically detects and handles Google CAPTCHA challenges:
- **Automatic Detection**: Instantly detects when CAPTCHA appears
- **Clear Instructions**: Shows what to do in the terminal
- **Auto-Resume**: Automatically continues when CAPTCHA is solved (no manual Enter press needed!)
- **Progress Updates**: Shows elapsed time every 10 seconds
- **Smart Polling**: Checks every 2 seconds for resolution
- **Timeout Protection**: 5-minute maximum wait with fallback

### Data Directory

All data is saved in the `spider_output/` folder in your current working directory:
- Profile URLs: `spider_output/profile_urls.txt`
- Exported profiles: `spider_output/profiles_YYYYMMDD_HHMMSS.csv/json/xlsx`
- Logs: `logs/linkedin-spider.log`

## ⚠️ Legal & Ethical Considerations

- **Terms of Service**: This tool is for educational purposes. Always comply with LinkedIn's Terms of Service.
- **Rate Limiting**: Use appropriate delays to avoid overwhelming servers.
- **Privacy**: Respect privacy. Only collect publicly available information.
- **Usage**: Use this tool responsibly and ethically.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with [Selenium](https://www.selenium.dev/), [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), and [Poetry](https://python-poetry.org/).

---

Made with ❤️ for data professionals
