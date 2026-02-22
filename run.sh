#!/bin/bash

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Activate and install requirements only if we just created it
    source "$VENV_DIR/bin/activate"

    if [ -f "requirements.txt" ]; then
        echo "Installing requirements..."
        python3 -m pip install -r requirements.txt
    else
        echo "requirements.txt not found, skipping install."
    fi
else
    echo "Virtual environment already exists. Skipping creation."
    source "$VENV_DIR/bin/activate"
fi

echo "Starting photo picker..."
python3 main.py
deactivate
