$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pyinstaller .\mouthclick.spec --clean --noconfirm

Write-Host "Build finalizado. Verifique a pasta dist\\MouthClick."
