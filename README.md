# 🕷️ LinkedIn Spider

<div align="center">

![LinkedIn Spider](https://img.shields.io/badge/LinkedIn-Spider-blue?style=for-the-badge&logo=linkedin)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Manager-blue?style=for-the-badge&logo=poetry)](https://python-poetry.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**A professional CLI tool for scraping LinkedIn profiles via Google Search**

> **📦 PyPI Package Name:** This project is available on PyPI as [`linkedin-tarantula`](https://pypi.org/project/linkedin-tarantula/) because `linkedin-spider` was already taken by another project. The GitHub repository remains `linkedin-spider`.

</div>

---

## 📖 Overview

LinkedIn Spider is a powerful, user-friendly command-line tool that helps you collect and analyze LinkedIn profiles at scale. By leveraging Google Search instead of direct LinkedIn scraping, it significantly reduces the risk of account restrictions while providing comprehensive profile data.

## ✨ Features

- 🔍 **Smart Search** - Find profiles via Google Search to avoid LinkedIn rate limits
- 🎨 **Beautiful CLI** - Interactive arrow-key menu navigation with ASCII art
- 📊 **Data Export** - Export to CSV, JSON, or Excel formats
- 🔐 **Secure** - Environment-based configuration for credentials
- 🌐 **VPN Support** - Optional IP rotation for enhanced privacy
- ⚡ **Fast & Efficient** - Progress tracking and batch processing
- 🛡️ **Anti-Detection** - Random delays, user agents, and human-like behavior
- 🤖 **CAPTCHA Handler** - Automatic CAPTCHA detection with auto-resume
- 🎮 **Interactive Menu** - Navigate with arrow keys (↑↓) and Enter

## 📦 Installation

### Option 1: PyPI Installation (Recommended)

> **Note:** The PyPI package is named `linkedin-tarantula` (not `linkedin-spider`) because the latter name was already taken.

```bash
# Install from PyPI
pip install linkedin-tarantula

# Or with Excel export support
pip install linkedin-tarantula[excel]
```

This installs the `linkedin-spider` command globally.

### Option 2: Quick Install from Source

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

### Option 3: Development Installation

```bash
# Install from source with Poetry
poetry install

# Optional: Install with Excel support
poetry install -E excel

# Activate the virtual environment
poetry shell
```

### Option 4: Install from GitHub (Direct)

```bash
# Install directly from GitHub
pip install git+https://github.com/alexcolls/linkedin-spider.git

# Or with Excel support
pip install "linkedin-spider[excel] @ git+https://github.com/alexcolls/linkedin-spider.git"
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
# If installed from PyPI (pip install linkedin-tarantula)
linkedin-spider

# If installed from source with system mode
linkedin-spider

# If installed with development mode
./run.sh

# Or with Poetry directly
poetry run python -m linkedin_spider
```

### Interactive Mode

The CLI provides an interactive menu with ASCII art and arrow-key navigation:

```bash
linkedin-spider  # or ./run.sh for development
```

**Navigation:**

- Use **↑↓ arrow keys** to navigate
- Press **Enter** to select
- Or type the **number** directly

Menu options:

1. 🔍 Search & Collect Profile URLs
2. 📊 Scrape Profile Data
3. 🤝 Auto-Connect to Profiles
4. 📁 View/Export Results
5. ⚙️ Configure Settings
6. ❓ Help
7. 🚪 Exit

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

All data is saved in the `data/` folder in your current working directory:

- Profile URLs: `data/profile_urls.txt`
- Exported profiles: `data/profiles_YYYYMMDD_HHMMSS.csv/json/xlsx`
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

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/alexcolls/linkedin-cv/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alexcolls/linkedin-cv/discussions)

---

## ⭐ Show Your Support

If this project helped you, please consider:

- ⭐ **Starring the repository**
- 🐛 **Reporting bugs**
- 💡 **Suggesting features**
- 🤝 **Contributing code**
- 📢 **Sharing with others**

---

                                                    |
                                                    |
                                                    |
                                                    |
                                                    |
                                                    |
                                                    |
                                        ____        |              ,
                                       /---.'.__    |        ____//
                                            '--.\   |       /.---'
                                       _______  \\  |      //
                                     /.------.\  \| |    .'/  ______
                                    //  ___  \ \ ||/|\  //  _/_----.\__
                                   |/  /.-.\  \ \:|< >|// _/.'..\   '--'
                                      //   \'. | \'.|.'/ /_/ /  \\
                                     //     \ \_\/" ' ~\-'.-'    \\
                                    //       '-._| :H: |'-.__     \\
                                   //           (/'==='\)'-._\     ||
                                   ||                        \\    \|
                                   ||                         \\    '
                                   |/                          \\
                                                                ||
                                                                ||
                                                                \\
                                                                 '
                   ╔════════════════════════════════════════════════════╪═╪═╪══════════╗
                   ║                                                                   ║
                   ║    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ ██╗███╗   ██╗     ║
                   ║    ██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗██║████╗  ██║     ║
                   ║    ██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██║  ██║██║██╔██╗ ██║     ║
                   ║    ██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██║  ██║██║██║╚██╗██║     ║
                   ║    ███████╗██║██║ ╚████║██║  ██╗███████╗██████╔╝██║██║ ╚████║     ║
                   ║    ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═══╝     ║
                   ║                                                                   ║
                   ║    ███████╗██████╗ ██╗██████╗ ███████╗██████╗      ^.-.^          ║
                   ║    ██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗    '^\+/^`         ║
                   ║    ███████╗██████╔╝██║██║  ██║█████╗  ██████╔╝    '/`"'\`         ║
                   ║    ╚════██║██╔═══╝ ██║██║  ██║██╔══╝  ██╔══██╗                    ║
                   ║    ███████║██║     ██║██████╔╝███████╗██║  ██║                    ║
                   ║    ╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝                    ║
                   ║    ═══╪══╪═╪═╪═══╪════════════════════════════════════════════    ║
                   ║                                                                   ║
                   ║               Professional Network Profile Scraper                ║
                   ║                ━━━ Weaving Through Networks ━━━                   ║
                   ║                                                                   ║
                   ╚═══════════════════════════════════════════════════════════════════╝

---

<p align="center">
  <b>Made with ❤️ and 🐍 Python</b><br>
  <i>Get Linkedin profiles at scale</i>
</p>

<p align="center">
  <sub>© 2022 LinkedIn Spider | MIT License</sub>
</p>
