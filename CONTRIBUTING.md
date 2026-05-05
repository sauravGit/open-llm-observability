# Contributing to open-llm-observability

Thank you for your interest in contributing! This project is in active RFC phase and all forms of contribution are welcome.

---

## Ways to Contribute

- **RFC Feedback** — Open a [Discussion](../../discussions) to comment on metric naming, scope, or OTEL mapping
- **Bug Reports** — Open an [Issue](../../issues) using the bug report template
- **Feature Requests** — Open an [Issue](../../issues) using the feature request template
- **Pull Requests** — Implement SDK features, add backend adapters, improve docs
- **Backend Adapters** — Implement exporters for Prometheus, Grafana, Datadog, GCP
- **Examples** — Add instrumentation examples for OpenAI, Anthropic, Vertex AI

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/sauravGit/open-llm-observability.git
cd open-llm-observability/sdk/python

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Code Style

- Python: formatted with `ruff`, type-checked with `mypy`
- All public functions must have docstrings
- All metric names must follow the `gen_ai.*` namespace defined in RFC.md
- Do not introduce new metric names without a corresponding RFC update

```bash
# Run linter
ruff check sdk/python/

# Run type checker
mypy sdk/python/open_llm_obs/

# Run tests
pytest sdk/python/tests/
```

---

## Pull Request Guidelines

1. Fork the repo and create a branch: `git checkout -b feat/your-feature`
2. Make your changes with clear, atomic commits
3. Use conventional commit messages: `feat:`, `fix:`, `docs:`, `chore:`
4. Ensure all tests pass and linting is clean
5. Open a PR with a clear description of what you changed and why
6. Reference any related Discussion or Issue in your PR description

---

## RFC Process

For changes to the canonical metric schema, span names, or interoperability rules:

1. Open a Discussion in the [RFC category](../../discussions) first
2. Get feedback from maintainers and community
3. Update RFC.md in a PR once consensus is reached
4. SDK changes that implement an RFC update should reference the RFC in the commit message

---

## Code of Conduct

Be respectful, constructive, and collaborative. This is a community project.

---

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
