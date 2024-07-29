#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

# install pip packages globally
sudo pip install --quiet -r requirements.txt --break-system-packages
echo "=> Installed pip packages"

cat << EOF | sudo tee /etc/systemd/system/stratopi-communication.service > /dev/null
[Unit]
Description=StratoPi Communication
After=multi-user.target postgresql.service

[Service]
User=root
WorkingDirectory=/home/pi/stratopi/software/communication
ExecStart=/usr/bin/python /home/pi/stratopi/software/communication/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
EnvironmentFile=/etc/environment

[Install]
WantedBy=multi-user.target
EOF
echo "=> Created systemd service 'stratopi-communication.service'"

sudo systemctl daemon-reload
echo "=> Reloaded systemctl daemon"
sudo systemctl enable stratopi-communication.service
echo "=> Enabled systemd service 'stratopi-communication.service'"
sudo systemctl restart stratopi-communication.service
echo "=> Restarted systemd service 'stratopi-communication.service'"
