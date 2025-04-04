#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root"
  exit 1
fi

read -p "Project directory (e.g. /var/www/fms): " PROJECT_DIR
read -p "Flask app file (e.g. app.py): " FLASK_FILE
read -p "Linux user (e.g. www-data): " LINUX_USER
read -p "Your domain (leave blank for no HTTPS): " DOMAIN

SERVICE_NAME="flask_app"
SOCK_FILE="$PROJECT_DIR/$SERVICE_NAME.sock"

# Ensure Python and Git are installed
apt update && apt install -y python3 python3-venv python3-pip git nginx

cd "$PROJECT_DIR" || exit 1

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
[ -f requirements.txt ] && pip install -r requirements.txt || echo "⚠️ No requirements.txt found!"

# Create wsgi.py
cat <<EOF > wsgi.py
from ${FLASK_FILE%.py} import app

if __name__ == "__main__":
    app.run()
EOF

# Create Gunicorn service
cat <<EOF > /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Gunicorn Flask Service
After=network.target

[Service]
User=$LINUX_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$SOCK_FILE wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# Start and enable Gunicorn
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Create Nginx config
cat <<EOF > /etc/nginx/sites-available/$SERVICE_NAME
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:$SOCK_FILE;
    }
}
EOF

# Link to sites-enabled
ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/

# Remove default Nginx site
rm -f /etc/nginx/sites-enabled/default

# Restart Nginx
systemctl restart nginx

# Set up HTTPS
if [[ -n "$DOMAIN" ]]; then
    apt install -y certbot python3-certbot-nginx
    certbot --nginx -d "$DOMAIN"
    echo "✅ HTTPS enabled!"
else
    echo "ℹ️ Skipping HTTPS setup."
fi

echo "🎉 Your Flask app is now online!"
