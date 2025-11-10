# 📦 PyPI Publishing Setup Guide

This guide explains how to publish **linkedin-spider** to PyPI both manually and automatically via GitHub Actions.

> **Note:** The PyPI package name is `linkedin-tarantula` (not `linkedin-spider`) because that name was already taken by another project. The CLI command remains `linkedin-spider`.

---

## 🔐 Setup GitHub Secrets

To use the automated workflow, you need to add your PyPI API token to GitHub Secrets:

### 1. Get your PyPI API Token

1. Go to [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
2. Click **"Add API token"**
3. Name it `linkedin-spider-github`
4. Scope: **"Entire account"** (or project-specific after first upload)
5. **Copy the token** (starts with `pypi-`)

### 2. Add Secret to GitHub

1. Go to your repository: `https://github.com/YOUR_USERNAME/linkedin-spider`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click **"Add secret"**

### 3. (Optional) TestPyPI Token

For testing, create a token at [https://test.pypi.org/manage/account/token/](https://test.pypi.org/manage/account/token/) and add it as `TEST_PYPI_API_TOKEN`.

---

## 🚀 Publishing Methods

### Method 1: Automatic (via GitHub Release) ⭐ Recommended

1. Update version in `pyproject.toml`:
   ```bash
   poetry version patch  # or minor, major
   ```

2. Commit and push:
   ```bash
   git add pyproject.toml
   git commit -m "🔖 Bump version to $(poetry version -s)"
   git push
   ```

3. Create a GitHub Release:
   - Go to **Releases** → **"Create a new release"**
   - Tag: `v0.1.0` (match pyproject.toml version)
   - Title: `v0.1.0 - Initial Release`
   - Description: Changelog notes
   - Click **"Publish release"**

4. The workflow will automatically:
   - Build the package
   - Publish to PyPI
   - Make it available via `pip install linkedin-tarantula`

### Method 2: Manual Workflow Trigger

1. Go to **Actions** → **📦 Publish to PyPI**
2. Click **"Run workflow"**
3. Choose environment: `pypi` or `testpypi`
4. Click **"Run workflow"**

### Method 3: Manual Local Publishing

1. Configure PyPI token locally:
   ```bash
   poetry config pypi-token.pypi pypi-YOUR_TOKEN_HERE
   ```

2. Build and publish:
   ```bash
   poetry build
   poetry publish
   ```

---

## 📋 Pre-Publishing Checklist

Before publishing, ensure:

- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated
- [ ] All tests pass: `poetry run pytest`
- [ ] Code formatted: `poetry run black .`
- [ ] Linting clean: `poetry run ruff check .`
- [ ] Type checking: `poetry run mypy src/`
- [ ] `README.md` is up to date
- [ ] Author email is correct in `pyproject.toml`
- [ ] License file exists

---

## 🔄 Version Management

Use Poetry's version command:

```bash
# Patch release (0.1.0 → 0.1.1)
poetry version patch

# Minor release (0.1.0 → 0.2.0)
poetry version minor

# Major release (0.1.0 → 1.0.0)
poetry version major

# Specific version
poetry version 1.2.3
```

---

## 🧪 Testing with TestPyPI

Before publishing to PyPI, test with TestPyPI:

```bash
# Configure TestPyPI
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi pypi-YOUR_TEST_TOKEN

# Build and publish to TestPyPI
poetry build
poetry publish -r testpypi

# Test installation
pip install --index-url https://test.pypi.org/simple/ linkedin-tarantula
```

---

## 🐛 Troubleshooting

### "Invalid authentication"
- Verify token is correct and starts with `pypi-`
- Check token hasn't expired
- Ensure token has correct scope

### "File already exists"
- Can't re-upload same version
- Bump version and try again
- PyPI doesn't allow replacing versions

### "Package name already taken"
- Choose a different name in `pyproject.toml`
- Or request name transfer from PyPI support

---

## 📚 Resources

- [Poetry Publishing Docs](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
- [PyPI Help](https://pypi.org/help/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
