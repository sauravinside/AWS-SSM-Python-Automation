#!/bin/bash
echo "Installing Grafana..."
sudo apt update -y
sudo apt install -y grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
echo "Grafana installation complete!"