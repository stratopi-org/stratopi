#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

# install pip packages globally
sudo pip install --quiet -r requirements.txt
echo "✅ Installed pip packages"

cat << EOF | sudo tee /etc/systemd/system/stratopi-battery.service > /dev/null
[Unit]
Description=StratoPi Battery
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/home/pi/stratopi/software/battery
ExecStart=/usr/bin/python /home/pi/stratopi/software/battery/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
EnvironmentFile=/etc/environment

[Install]
WantedBy=multi-user.target
EOF
echo "✅ Created systemd service 'stratopi-battery.service'"

sudo systemctl daemon-reload
echo "✅ Reloaded systemctl daemon"
sudo systemctl enable stratopi-battery.service
echo "✅ Enabled systemd service 'stratopi-battery.service'"
sudo systemctl restart stratopi-battery.service
echo "✅ Restarted systemd service 'stratopi-battery.service'"
