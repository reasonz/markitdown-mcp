#!/bin/bash

echo 'Installing Python dependencies for OCR...'
echo 'Installing uv'
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'Using uv to install markitdown and other dependencies'
uv sync
echo 'Finished install Python dependencies'