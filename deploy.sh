#!/bin/bash
set -euo pipefail

cd /home/isucon/src
git pull --ff-only origin main
sudo rsync -a --delete --exclude .venv /home/isucon/src/webapp/ /home/isucon/webapp/python/
sudo systemctl restart isuride-python
sudo systemctl is-active isuride-python