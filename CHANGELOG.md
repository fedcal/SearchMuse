# Changelog

All notable changes to SearchMuse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project documentation site published via GitHub Pages.
- GitHub Actions workflows: `Deploy Docs` (push on `master`) and `Docs Check`
  (PR validation with `mkdocs build --strict`).
- Standard project files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `CHANGELOG.md`.
- `social` and `edit_uri` entries in `mkdocs.yml`.

### Changed
- `mkdocs.yml` and `pyproject.toml` URLs now point to the real
  `fedcal/SearchMuse` repository.
- Docs deploy workflow now installs the `[docs]` extras from `pyproject.toml`
  and uses pip cache.

### Removed
- Tracked `site/` build artifacts (now ignored via `.gitignore`).
- Duplicate `docs/000_index.md` (the homepage is `docs/index.md`).
- Internal development note `docs/003_it/001_functional/000_INDEX.md`
  containing local filesystem paths.

## [0.1.0] - 2026-02-28

### Added
- Initial pre-alpha release of SearchMuse: CLI, models, chat creation,
  context handling, hexagonal architecture skeleton.
- Functional and technical documentation (EN + IT) under `docs/`.

[Unreleased]: https://github.com/fedcal/SearchMuse/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fedcal/SearchMuse/releases/tag/v0.1.0
