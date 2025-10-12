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

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/alexcolls/linkedin-spider.git
cd linkedin-spider

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

### Interactive Mode

```bash
# Launch interactive CLI
linkedin-spider
```

### Command-Line Mode

```bash
# Search for profiles
linkedin-spider search "Python Developer" "San Francisco" --max-pages 10

# Scrape profiles
linkedin-spider scrape --urls data/profile_urls.txt --output results --format csv
```

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
