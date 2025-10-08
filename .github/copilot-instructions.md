# Copilot Instructions for camelgo

This project implements an RL agent for the CamelUp board game. The codebase is minimal and structured for rapid prototyping and experimentation.

## Architecture Overview
- **Main package:** All source code is under `src/camelgo/`.
- **Entrypoints:**
  - `main.py`: CLI utility for generating random numbers (demo/placeholder).
  - `__init__.py`: Defines the main entrypoint for the package (`main()`), used by the CLI script.
- **Project metadata:** Managed via `pyproject.toml`.
  - The CLI command `camelgo` runs `camelgo.main()` from `__init__.py`.

## Developer Workflows
- **Run CLI locally:**
  ```sh
  python src/camelgo/main.py --min 1 --max 10
  ```
- **Install as CLI tool:**
  ```sh
  pip install .
  camelgo
  ```
- **Build system:** Uses `uv_build` (see `pyproject.toml`).
- **Python version:** Requires Python >=3.8.

## Patterns & Conventions
- **Single package:** All code is in one package; add new modules under `src/camelgo/`.
- **Entrypoint convention:** The CLI tool is mapped to `camelgo:main` in `pyproject.toml`.
- **Minimal dependencies:** No external dependencies by default; add to `pyproject.toml` as needed.
- **No tests or RL logic yet:** The current codebase is a scaffold. Add RL agent logic and tests in new modules under `src/camelgo/`.

## Key Files
- `src/camelgo/main.py`: CLI demo, replace with RL agent logic.
- `src/camelgo/__init__.py`: Package entrypoint.
- `pyproject.toml`: Project config, CLI mapping, dependencies.
- `README.md`: Project overview.

## Example: Adding RL Agent Logic
- Create new modules in `src/camelgo/` (e.g., `agent.py`, `game.py`).
- Update `main.py` to run RL agent code.
- Register new CLI commands in `pyproject.toml` if needed.

---
**For AI agents:**
- Follow the single-package structure.
- Use `pyproject.toml` for CLI and dependency management.
- Keep code modular and add new features in `src/camelgo/`.
- Update this file as new conventions or workflows emerge.
