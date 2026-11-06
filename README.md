# 🕷️ LinkedIn Spider

<div align="center">

![LinkedIn Spider](https://img.shields.io/badge/LinkedIn-Spider-blue?style=for-the-badge&logo=linkedin)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Manager-blue?style=for-the-badge&logo=poetry)](https://python-poetry.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**A professional CLI tool for scraping LinkedIn profiles via Google Search**

> **📦 PyPI Package Name:** This project is available on PyPI as [`linkedin-tarantula`](https://pypi.org/project/linkedin-tarantula/) because `linkedin-spider` was already taken by another project. The GitHub repository remains `linkedin-spider`.

</div>

---

## 📖 Overview

LinkedIn Spider is a command-line tool that finds LinkedIn profiles through Google Search, then opens each one in a browser to collect its data. It runs on one machine, with delays between profiles.

## ✨ Features

- 🔍 **Smart Search** - Find profiles via Google Search
- 🎨 **Beautiful CLI** - Interactive arrow-key menu navigation with ASCII art
- 📊 **Data Export** - Export to CSV, JSON, or Excel formats, safe to open in a spreadsheet
- 🔐 **Secure** - Credentials from the environment, and output files only you can read
- 🛑 **Stops When Blocked** - Stops at a login wall or after repeated failures, ready to resume
- 🤖 **CAPTCHA Handler** - Detects CAPTCHAs, waits for you to solve them, then carries on
- 🎮 **Interactive Menu** - Navigate with arrow keys (↑↓) and Enter
- 💾 **Resume Support** - Interrupt and resume scraping sessions without losing anything
- 🤝 **Guided Connect** - Send connection requests one at a time, confirming each person
- 🔍 **Dry Run Mode** - Preview URLs before scraping
- 📊 **Smart Statistics** - Detailed progress and success rate tracking
- 🔧 **Debug Mode** - Verbose logging for troubleshooting

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

# Run it
poetry run linkedin-spider
```

### Option 4: Install from GitHub (Direct)

```bash
# Install directly from GitHub
pip install git+https://github.com/alexcolls/linkedin-spider.git

# Or with Excel support
pip install "linkedin-tarantula[excel] @ git+https://github.com/alexcolls/linkedin-spider.git"
```

## ⚙️ Configuration

### 1. Environment Variables

```bash
cp .env.sample .env
# Edit .env with your LinkedIn credentials
```

### 2. Configuration File

Edit `config.yaml` for advanced settings (delays, export format, logging, etc.)

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

# Dry run - preview URLs without scraping
linkedin-spider scrape --urls data/profile_urls.txt --dry-run

# Resume interrupted scraping
linkedin-spider scrape --resume session_20250110_143022

# Custom session name with debug mode
linkedin-spider scrape --urls data/profile_urls.txt --session my-scrape --debug

# List active sessions
linkedin-spider sessions

# Clean up session files
linkedin-spider sessions --cleanup

# Show version
linkedin-spider version
```

## 🚀 Advanced Features

### Resume Interrupted Scraping

If your scraping session is interrupted (Ctrl+C, network issues, etc.), you can resume exactly where you left off:

```bash
# Start scraping
linkedin-spider scrape --urls data/profile_urls.txt

# If interrupted, list sessions to find your session name
linkedin-spider sessions

# Resume from where you left off
linkedin-spider scrape --resume session_20250110_143022
```

Each profile is saved to the session as soon as it's scraped, so an interruption loses nothing. Ctrl+C exports what you have so far, and resuming retries failed URLs and exports the whole session.

A run also stops by itself, ready to resume, if LinkedIn shows a login wall or 5 profiles fail in a row.

### Guided Connect

Menu option 3 goes through your collected profiles and asks before each request, showing the person's name. It sends at most 10 requests per run. If it can't find a Connect button clearly belonging to that person, it skips them.

### Dry Run Mode

Preview what will be scraped before starting:

```bash
linkedin-spider scrape --urls data/profile_urls.txt --dry-run
```

This shows:
- ✅ List of URLs to scrape
- ✅ Total count
- ✅ No actual scraping or login

### Debug Mode

Get detailed logs for troubleshooting:

```bash
linkedin-spider scrape --urls data/profile_urls.txt --debug
```

### Session Management

View all active progress sessions:

```bash
# List all sessions with statistics
linkedin-spider sessions

# Delete all session files, including unfinished ones
linkedin-spider sessions --cleanup
```

### Custom Session Names

Use memorable session names instead of timestamps:

```bash
linkedin-spider scrape --urls data/profile_urls.txt --session my-project-name
linkedin-spider scrape --resume my-project-name
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
- **Headless Mode**: Stops the search straight away, since nobody can solve a CAPTCHA there

### Data Directory

All data is saved in the `data/` folder in your current working directory:

- Profile URLs: `data/profile_urls.txt`
- Exported profiles: `data/profiles_YYYYMMDD_HHMMSS.csv/json/xlsx`
- Session progress, including scraped profiles: `data/.progress_<session>.json`
- Logs: `logs/linkedin-spider.log`

Exports and session files are readable only by you, because they hold personal data.

### Distributed Deployment (Unsupported)

The Docker and Kubernetes files, the `worker` command, cookie extraction and VPN switching are unsupported, and the distributed setup doesn't work. They're kept for reference, and only security problems get fixed. See [README-K8S.md](README-K8S.md).

## ⚠️ Legal & Ethical Considerations

- **Terms of Service**: LinkedIn's User Agreement prohibits automated access, and using this tool can get your account restricted. You're responsible for how you use it.
- **Personal Data**: Scraped profiles are personal data. Laws such as GDPR and CCPA may apply to collecting, storing and using them, even when the profile is public.
- **Connection Requests**: Requests reach real people. Only send ones you'd send by hand.
- **Rate Limiting**: Keep the delays. They limit the load you put on the site.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with [Selenium](https://www.selenium.dev/), [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), and [Poetry](https://python-poetry.org/).

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/alexcolls/linkedin-spider/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alexcolls/linkedin-spider/discussions)

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
