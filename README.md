# camelgo

A Python implementation of the **Camel Up** board game (Second Edition), featuring a robust game engine, an interactive web interface, and a foundation for Reinforcement Learning (RL) agents.

## 🐫 Features

- **Complete Game Logic**: Fully implements the rules of Camel Up (2nd Edition), including:
  - Camel movement and stacking mechanics.
  - Crazy Camels moving in reverse.
  - Leg and Game betting.
  - Cheering/Booing tiles.
- **Interactive Web UI**: A Dash-based web application to play and visualize the game state in real-time.
- **Modern Tech Stack**:
  - **Python 3.12+**
  - **Pydantic**: For robust, type-safe domain modeling and state serialization.
  - **Dash**: For the frontend interface.
  - **Podman/Docker**: For containerized deployment.
  - **uv**: For fast Python package and dependency management.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)
- Podman or Docker (optional, for containerized run)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gokhanceyhan/camelgo.git
   cd camelgo
   ```

2. **Install dependencies:**
   Using `uv` (recommended):
   ```bash
   uv venv
   uv sync
   ```

## 🎮 Running the Game

### Local Dash App
To start the interactive web interface locally:

```bash
python src/camelgo/application/dash_app.py
```
Open your browser and navigate to `http://localhost:8080`.

### Using Containers (Podman/Docker)

1. **Build the image:**
   ```bash
   podman machine start
   podman build -t camelgo:latest .
   ```

2. **Run the container:**
   ```bash
   podman run -it --rm -p 8080:8080 -v $(pwd)/src:/app/src camelgo:latest
   ```
   The `-v` flag mounts your source code, allowing for live updates during development.

## 🧪 Development

### Project Structure
```
src/camelgo/
├── application/    # Application layer (Dash app, CLI)
├── domain/         # Domain logic (Game, Leg, Camel, Player, etc.)
└── ...
tests/              # Unit tests
```

### Running Tests
The project uses `pytest` for testing.

```bash
pytest tests/
```

## 📝 License
[MIT](LICENSE)
