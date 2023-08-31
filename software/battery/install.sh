#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

# install pip packages globally
sudo pip install -r requirements.txt

cat << EOF | sudo tee /etc/systemd/system/stratopi-battery.service > /dev/null
Description=StratoPi Battery
After=network.target

[Service]
ExecStart=/usr/bin/python /home/pi/stratopi/software/battery/app.py
WorkingDirectory=/home/pi/stratopi/software/battery
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable stratopi-battery.service
sudo systemctl restart stratopi-battery.service
