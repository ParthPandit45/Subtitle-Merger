# Contributing to merge_subs

Thank you for your interest in contributing to `merge_subs`! We welcome contributions from bug reports to performance enhancements.

---

## Getting Started

### Prerequisites
- **Python**: 3.9 or newer.
- **FFmpeg & FFprobe**: Installed and accessible on your system `PATH` (or via WinGet: `winget install Gyan.FFmpeg`).
- **Git**: Installed and configured.

### Setting Up Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/ParthPandit45/Subtitle-Merger.git
   cd Subtitle-Merger
   ```

2. (Optional) Create a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

---

## Running Tests

The test suite runs with zero third-party dependencies using Python's built-in `unittest`:

```bash
# Run all tests:
python -m unittest discover -s tests -v

# Or with pytest (if installed):
pytest
```

All contributions must pass all existing tests and include test coverage for new functionality.

---

## Building the Standalone Executable

To verify packaging and build the standalone Windows `.exe`:

```bash
python build_exe.py
```

The resulting binary will be placed at `dist/Subtitle-Merger.exe`.

---

## Code Style & Architecture

- **Standard Library First**: Core functionality should remain dependency-free so the CLI can be run immediately without `pip install`.
- **Atomic Operations**: Subtitle embedding must remain strictly lossless and safe (using `.part` intermediate files, stream validation, and atomic replace).
- **Type Annotations**: All new functions should have Python type annotations.
- **Docstrings**: Maintain clear docstrings for modules and functions.

---

## Submitting Pull Requests

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with descriptive messages:
   ```bash
   git commit -m "feat: add support for XYZ subtitle format"
   ```
3. Push to your branch and open a Pull Request against `main`.
