# Contributing to LinkedIn Spider

Thank you for considering contributing to LinkedIn Spider! 🎉

## Code of Conduct

Be respectful, inclusive, and professional. We're here to build something great together.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/alexcolls/linkedin-spider/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain how it would benefit users

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Ensure code quality:
   ```bash
   black linkedin_spider/
   ruff check linkedin_spider/
   mypy linkedin_spider/
   pytest
   ```
6. Commit with emoji prefixes:
   - ✨ `:sparkles:` - New feature
   - 🐛 `:bug:` - Bug fix
   - 📝 `:memo:` - Documentation
   - ♻️ `:recycle:` - Refactoring
   - ✅ `:white_check_mark:` - Tests
   - 🎨 `:art:` - UI/UX improvements
7. Push to your fork
8. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/linkedin-spider.git
cd linkedin-spider

# Install dependencies
poetry install --with dev

# Activate environment
poetry shell

# Run tests
pytest

# Format code
black linkedin_spider/

# Lint
ruff check linkedin_spider/
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Keep functions focused and single-purpose
- Add comments for complex logic

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Use pytest fixtures for common setup
- Mock external services (Selenium, API calls)

## Questions?

Open an issue or reach out to the maintainers. We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
