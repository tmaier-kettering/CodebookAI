# Contributing to CodebookAI

Thank you for your interest in contributing to CodebookAI! This guide explains
how to set up your development environment, run the test suite, and submit
changes.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Running the Application Locally](#running-the-application-locally)
3. [Running the Tests](#running-the-tests)
4. [Project Structure](#project-structure)
5. [Coding Conventions](#coding-conventions)
6. [Reporting Bugs](#reporting-bugs)
7. [Proposing Changes](#proposing-changes)
8. [Getting Support](#getting-support)

---

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or later |
| tkinter | bundled with most Python installers; see note below |

> **Linux note:** tkinter is a separate package on many distros.
> Install it with:
> ```bash
> # Ubuntu / Debian
> sudo apt-get install python3-tk
> # Fedora / RHEL
> sudo dnf install python3-tkinter
> ```

### Clone and install dependencies

```bash
git clone https://github.com/tmaier-kettering/CodebookAI.git
cd CodebookAI

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows PowerShell

# Install runtime dependencies
pip install -r requirements.txt

# Install development/testing dependencies
pip install -r requirements-dev.txt
```

---

## Running the Application Locally

```bash
python main.py
```

The application requires an OpenAI API key.  On first launch, go to
**File → Settings** and paste your key.  The key is stored in your OS
credential vault (Windows Credential Manager / macOS Keychain / Linux
Secret Service) and is never written to disk in plain text.

---

## Running the Tests

The test suite uses [pytest](https://docs.pytest.org/) and covers the
application's core logic without requiring a live OpenAI API key or a
graphical display.

```bash
# Run the full test suite
pytest

# Run a specific file
pytest tests/test_batch_creation.py

# Run a specific test class or function
pytest tests/test_batch_parsing.py::TestSafeParseModelText
pytest tests/test_batch_parsing.py::TestSafeParseModelText::test_valid_json_returns_dict_no_error

# Show verbose output and full tracebacks
pytest -v --tb=long
```

### What the tests cover

| File | Coverage area |
|------|---------------|
| `test_batch_creation.py` | JSONL batch generation — prompt construction, schema building, `forbid_additional_props`, non-ASCII text, edge cases |
| `test_batch_parsing.py` | Result parsing (`_safe_parse_model_text`), OpenAI client creation, `get_batch_results` with mocked API (success, auth failure, rate limit, timeout, malformed output, fenced JSON) |
| `test_data_conversion.py` | `make_str_enum`, `to_long_df` (including multi-label explode), `join_datasets` |
| `test_data_import.py` | Delimiter sniffing, CSV/TSV/Excel reading, non-ASCII content, empty files, realistic fixture |
| `test_settings.py` | User config load/save/roundtrip, `get_setting` precedence |
| `test_reliability.py` | Cohen's kappa — perfect agreement, known value, edge cases (empty, mismatched lengths, single label, unicode labels) |

### Headless / CI environments

The tests do **not** open any GUI windows, so they run fine in headless
environments (GitHub Actions, Docker containers, SSH sessions).  If you
hit display-related errors, wrap the pytest invocation with `xvfb-run -a`:

```bash
sudo apt-get install -y xvfb
xvfb-run -a pytest
```

The project's GitHub Actions workflow does this automatically.

---

## Project Structure

```
CodebookAI/
├── main.py                     Entry point – creates the Tkinter root window
├── requirements.txt            Runtime dependencies
├── requirements-dev.txt        Test / development dependencies
├── pytest.ini                  Pytest configuration
│
├── batch_processing/           OpenAI Batch API workflow
│   ├── batch_creation.py       JSONL generation (pure, fully testable)
│   ├── batch_method.py         Batch submission / retrieval / result parsing
│   └── batch_error_handling.py Error reporting UI
│
├── live_processing/            Real-time classification
│   ├── single_label_live.py    Single-label pipeline
│   ├── multi_label_live.py     Multi-label pipeline
│   ├── reliability_calculator.py  Cohen's kappa (pure, fully testable)
│   ├── keyword_extraction_live.py
│   ├── correlogram.py
│   └── sampler.py
│
├── file_handling/              File I/O (mostly pure, fully testable)
│   ├── data_import.py          CSV / Excel reader + import-wizard GUI
│   └── data_conversion.py      make_str_enum, to_long_df, join_datasets
│
├── settings/                   Configuration
│   ├── config.py               Default constants
│   ├── user_config.py          JSON-based user settings (fully testable)
│   ├── secrets_store.py        OS keyring wrapper
│   └── models_registry.py      OpenAI model list cache
│
├── ui/                         Tkinter GUI components
│
├── tests/                      Automated test suite
│   ├── conftest.py             Shared fixtures; in-memory keyring setup
│   ├── fixtures/               Static data files used by tests
│   │   ├── sample_labels.csv
│   │   ├── sample_quotes.csv
│   │   └── realistic_dataset.csv
│   ├── test_batch_creation.py
│   ├── test_batch_parsing.py
│   ├── test_data_conversion.py
│   ├── test_data_import.py
│   ├── test_settings.py
│   └── test_reliability.py
│
├── example_dataset/            Bundled example data
├── assets/                     Images and icons
└── wiki/                       Documentation
```

---

## Coding Conventions

* **Python 3.10+** — the codebase uses `X | Y` union syntax in type annotations.
* **Type annotations** are used throughout; please annotate new public functions
  and classes.
* **Pydantic v2** is used for data validation; follow the existing
  `model_config = ConfigDict(...)` pattern.
* **No external side effects at module level** — avoid making network or file
  system calls at module import time.  (The existing `models_registry.py` is a
  known exception that is guarded with `try/except`.)
* Keep GUI code (tkinter) in the `ui/` package or in thin UI-layer functions.
  Business logic and data processing should be in separate, GUI-free modules
  so they can be unit-tested without a display.
* Match the docstring style already present in the file you are editing.

---

## Reporting Bugs

1. Check the [existing issues](https://github.com/tmaier-kettering/CodebookAI/issues)
   to see if the problem has already been reported.
2. If not, open a new issue and include:
   - A clear title and description of the problem.
   - Steps to reproduce, including the input data if applicable.
   - The Python version, OS, and CodebookAI version (or git commit hash).
   - Any error messages or stack traces from the console.

---

## Proposing Changes

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```
2. Make your changes and **add or update tests** in the `tests/` directory.
3. Verify the full test suite passes:
   ```bash
   pytest
   ```
4. Open a **pull request** against the `main` branch with a clear description
   of what was changed and why.

We use GitHub Actions to run the test suite automatically on every pull request.
A passing CI run is required before a PR can be merged.

---

## Getting Support

* **Documentation:** see the [wiki folder](./wiki/) for user guides.
* **Questions or ideas:** open a [GitHub Discussion](https://github.com/tmaier-kettering/CodebookAI/discussions)
  or a [GitHub Issue](https://github.com/tmaier-kettering/CodebookAI/issues).
* **Security vulnerabilities:** please report them privately via GitHub's
  [security advisory](https://github.com/tmaier-kettering/CodebookAI/security/advisories)
  feature rather than in a public issue.

---

*CodebookAI is an MIT-licensed open-source project. Contributions of all kinds
are welcome.*
