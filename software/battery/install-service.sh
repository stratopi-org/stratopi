#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

cat << EOF | sudo tee /etc/systemd/system/stratopi-battery.service > /dev/null
Description=StratoPi Battery
After=network.target

[Service]
ExecStart=app.py
WorkingDirectory=/home/pi/stratopi/software/battery
Restart=always
User=root
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable stratopi-battery.service
sudo systemctl start stratopi-battery.service
