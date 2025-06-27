#!/bin/bash

# Версия Python
PYTHON_VERSION=3.10.13

# Настройка pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

# Установка Python
pyenv install -s $PYTHON_VERSION
pyenv global $PYTHON_VERSION

# Установка pip
curl https://bootstrap.pypa.io/get-pip.py | python

# Установка зависимостей
pip install -r requirements.txt
