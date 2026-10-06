#!/bin/bash
set -euo pipefail

cd /home/isucon/src
git fetch origin main
git reset --hard origin/main

sudo rsync -a --delete --exclude .venv /home/isucon/src/webapp/ /home/isucon/webapp/python/
sudo rsync -a /home/isucon/src/webapp/sql/ /home/isucon/webapp/sql/
sudo chmod +x /home/isucon/webapp/sql/init.sh
sudo systemctl restart isuride-python
sudo systemctl is-active isuride-python