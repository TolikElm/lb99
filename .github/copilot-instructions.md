# Copilot Instructions

## Project

99-Luftballons is a desktop arcade game written in Python with Pygame. Keep changes focused on the game and preserve the existing German-language UI and documentation unless a task asks otherwise.

## Structure

- `main.py` owns the game loop, state transitions, spawning, input, HUD, and screens.
- `balloon.py` owns balloon sizes, movement, drawing, visibility, hit testing, and scoring accuracy.
- `effects.py` owns pop particles and floating score text.
- `sound.py` synthesizes and plays sounds through Pygame; the game has no external audio assets.
- `PLAN.md` describes intended mechanics; `README.md` documents gameplay and setup.

## Gameplay Invariants

- A round spawns at most 99 balloons and is won only after all 99 have spawned and none remain active.
- A balloon is clickable only when its center is above the bottom edge (`y < screen_height`).
- Game over occurs when an active balloon touches the top edge (`y - radius <= 0`).
- Hit accuracy decreases linearly from 1.0 at the center to 0.1 at the radius: `1.0 - 0.9 * (distance / radius)`. Clamp it to that range and round awarded points to one decimal place.
- Balloon tier data in `BALLOON_SPECS` determines its radius, base points, and color; keep those properties consistent when changing tiers or scoring.
- Keep audio generation optional so the game still runs when the system mixer is unavailable.

## Development

- Requires Python 3.9+ and Pygame (`pip install -r requirements.txt`).
- Run the game from this directory with `python main.py` (or `python3 main.py`).
- No automated test suite or test configuration is currently present. For gameplay changes, run the game and check the affected behavior; use focused Python checks for deterministic logic where practical.
- Keep runtime dependencies in `requirements.txt`. Avoid adding external assets unless the task requires them.
- Follow the existing lightweight module structure and avoid unrelated refactors.