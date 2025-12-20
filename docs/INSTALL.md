# VPS Install (Project #3, isolated)

These instructions assume Ubuntu 22.04/24.04, but work similarly elsewhere.

## 0) Create a separate Linux user (recommended)
```bash
sudo adduser sku_bot
sudo usermod -aG sudo sku_bot
```

## 1) Install system packages
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip postgresql postgresql-contrib
```

## 2) Create PostgreSQL DB + user (isolated)
```bash
sudo -u postgres psql
```
Inside psql:
```sql
CREATE USER sku_bot WITH PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
CREATE DATABASE sku_bot OWNER sku_bot;
\q
```

## 3) Upload project folder to VPS
Upload this whole repository into e.g. `/home/sku_bot/sku_profit_bot`.

## 4) Create venv + install requirements
```bash
cd /home/sku_bot/sku_profit_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5) Configure environment
```bash
cp .env.example .env
nano .env
```

Required:
- `BOT_TOKEN` (your bot token)
- `ADMIN_IDS` (your Telegram numeric user id(s))
- `DB_DSN` (points to the DB you created)
- `YOOKASSA_SHOP_ID` and `YOOKASSA_SECRET_KEY` (for payments)

## 6) Run once (test)
```bash
source .venv/bin/activate
python -m app.main
```

## 7) Run as a systemd service (recommended)
Create service:
```bash
sudo nano /etc/systemd/system/sku-profit-bot.service
```

Paste:
```ini
[Unit]
Description=SKU Profit Control Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=sku_bot
WorkingDirectory=/home/sku_bot/sku_profit_bot
EnvironmentFile=/home/sku_bot/sku_profit_bot/.env
ExecStart=/home/sku_bot/sku_profit_bot/.venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sku-profit-bot
sudo systemctl start sku-profit-bot
sudo systemctl status sku-profit-bot --no-pager
```

View logs:
```bash
sudo journalctl -u sku-profit-bot -f
```

## 8) Payments (YooKassa)
This bot uses a simple flow without webhooks:
- create payment via YooKassa
- send user a confirmation URL
- user presses “✅ I paid”
- bot checks status via YooKassa API and credits the SKU pack

So you **don’t** need a public webhook endpoint.

## 9) Backups
Postgres backup:
```bash
pg_dump -U sku_bot -h 127.0.0.1 sku_bot > backup_$(date +%F).sql
```
