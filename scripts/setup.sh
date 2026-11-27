#!/bin/bash
# One-time setup: creates a virtual environment and installs dependencies.
# Run from the project root: ./scripts/setup.sh
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it and add your OPENAI_API_KEY when you get to the voice phase."
fi

echo "Setup complete. Run the app with: ./scripts/run.sh"
