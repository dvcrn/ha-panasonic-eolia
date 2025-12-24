# Repository Guidelines

## Project Overview
This repository provides a Home Assistant custom integration for Panasonic Eolia air conditioners, exposing climate control and temperature sensors.

## Project Structure & Module Organization
- `custom_components/panasonic_eolia/` is the integration package loaded by Home Assistant.
- `custom_components/panasonic_eolia/eolia/` contains the API client (auth, device models, HTTP adapters).
- `config_flow.py`, `climate.py`, and `sensor.py` define the user setup flow and entity platforms.
- `manifest.json`, `strings.json`, and `translations/` hold Home Assistant metadata and UI text.
- `docker-compose.yml` is the dev container entrypoint; `pyproject.toml` and `uv.lock` capture Python metadata.

## Build, Test, and Development Commands
- `docker compose up` starts a Home Assistant container and mounts the local custom component (see `docker-compose.yml` for volume paths and env vars).
- No build step is required; changes are picked up on Home Assistant restart or container recreation.

## Coding Style & Naming Conventions
- Use 4-space indentation and standard Python conventions.
- Keep module names snake_case and aligned with Home Assistant patterns (e.g., `config_flow.py`, `climate.py`).
- Maintain the integration domain name `panasonic_eolia` in folder names and `manifest.json`.
- Centralize constants in `custom_components/panasonic_eolia/const.py` and avoid hard-coded strings in modules.

## Testing Guidelines
- There is no automated test suite in this repository yet.
- Manual validation: run `docker compose up`, add the Panasonic Eolia integration in the Home Assistant UI, and verify climate control plus temperature sensor updates.
- Authentication can use `PANASONIC_USERNAME`/`PANASONIC_PASSWORD` or token-based env vars; 2FA is not supported for username/password auth.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative statements without prefixes (example: `Add sensor platform for temperature monitoring`).
- Pull requests should include a concise change summary, testing notes, and linked issues when applicable; add screenshots if UI strings change.

## Security & Configuration Tips
- Keep credentials out of the repo; use environment variables or local Home Assistant config.
- Supported env vars in `docker-compose.yml` include `PANASONIC_ACCESS_TOKEN`, `PANASONIC_REFRESH_TOKEN`, and `PANASONIC_ID_TOKEN`.
