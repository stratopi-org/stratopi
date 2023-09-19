#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

# install pip packages globally
sudo pip install --quiet -r requirements.txt
echo "✅ Installed pip packages"

cat << EOF | sudo tee /etc/systemd/system/stratopi-location.service > /dev/null
[Unit]
Description=StratoPi Location
After=multi-user.target postgresql.service

[Service]
User=root
WorkingDirectory=/home/pi/stratopi/software/location
ExecStart=/usr/bin/python /home/pi/stratopi/software/location/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
EnvironmentFile=/etc/environment

[Install]
WantedBy=multi-user.target
EOF
echo "✅ Created systemd service 'stratopi-location.service'"

sudo systemctl daemon-reload
echo "✅ Reloaded systemctl daemon"
sudo systemctl enable stratopi-location.service
echo "✅ Enabled systemd service 'stratopi-location.service'"
sudo systemctl restart stratopi-location.service
echo "✅ Restarted systemd service 'stratopi-location.service'"
