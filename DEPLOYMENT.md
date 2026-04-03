# TailorCV Deployment Guide

## Deploy to 10.197.36.30

### Option 1: Direct Run (Quick Test)

```bash
# SSH to the server
ssh user@10.197.36.30

# Install dependencies
cd /path/to/TailorCv
pip3 install -r requirements.txt
pip3 install fastapi uvicorn python-multipart pymupdf

# Run the server
python3 api.py
# Server will be available at http://10.197.36.30:8000
```

### Option 2: Custom Port

To run on a different port (e.g., 5000):

```bash
# Edit api.py and change the port, or run with uvicorn directly:
uvicorn api:app --host 0.0.0.0 --port 5000
# Server will be available at http://10.197.36.30:5000
```

### Option 3: Background with nohup

```bash
nohup python3 api.py > tailorcv.log 2>&1 &
# Check logs: tail -f tailorcv.log
# Stop: pkill -f "python3 api.py"
```

### Option 4: Using screen (Persistent Session)

```bash
# Install screen if not available
sudo apt-get install screen

# Start a screen session
screen -S tailorcv

# Run the app
cd /path/to/TailorCv
python3 api.py

# Detach: Press Ctrl+A then D
# Reattach later: screen -r tailorcv
# Kill session: screen -X -S tailorcv quit
```

### Option 5: Systemd Service (Production)

Create `/etc/systemd/system/tailorcv.service`:

```ini
[Unit]
Description=TailorCV Resume Optimization Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/TailorCv
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="OPENAI_API_KEY=your-api-key-here"
ExecStart=/usr/bin/python3 /path/to/TailorCv/api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl start tailorcv
sudo systemctl enable tailorcv  # Auto-start on boot
sudo systemctl status tailorcv  # Check status
sudo journalctl -u tailorcv -f  # View logs
```

### Option 6: With Gunicorn (Production - Multiple Workers)

```bash
pip3 install gunicorn

# Run with 4 workers
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 7: Behind Nginx (Reverse Proxy)

Install nginx:
```bash
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/tailorcv`:

```nginx
server {
    listen 80;
    server_name 10.197.36.30;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/tailorcv /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Firewall Configuration

If the port is blocked:

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Environment Variables

Set the API key before running:

```bash
export OPENAI_API_KEY="sk-a698415989cc4588bb67ad3b2be41e00"
# Or add to ~/.bashrc for persistence
echo 'export OPENAI_API_KEY="sk-a698415989cc4588bb67ad3b2be41e00"' >> ~/.bashrc
```

## Verify Deployment

```bash
# From another machine
curl http://10.197.36.30:8000/

# Should return the HTML page
```

## Updating the App

```bash
# Pull latest changes
cd /path/to/TailorCv
git pull

# Restart service
sudo systemctl restart tailorcv
# OR if using screen/nohup:
pkill -f "python3 api.py"
nohup python3 api.py > tailorcv.log 2>&1 &
```

## Troubleshooting

1. **Port already in use:**
   ```bash
   sudo lsof -i :8000
   # Kill the process or use a different port
   ```

2. **Permission denied:**
   ```bash
   # Use sudo or change owner
   sudo chown -R $USER:$USER /path/to/TailorCv
   ```

3. **Module not found:**
   ```bash
   pip3 install -r requirements.txt --upgrade
   ```

4. **Check server logs:**
   ```bash
   tail -f tailorcv.log
   # OR
   sudo journalctl -u tailorcv -f
   ```
