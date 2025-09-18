#!/bin/bash

# Configure Nginx
sudo tee /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # Handle OPTIONS requests (CORS preflight)
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' 'http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com' always;
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
                add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept, Authorization' always;
                add_header 'Access-Control-Allow-Credentials' 'true' always;
                add_header 'Content-Length' 0;
                add_header 'Content-Type' text/plain;
                return 204;
            }

            # CORS headers for actual requests
            add_header 'Access-Control-Allow-Origin' 'http://eloquent-ai-frontend-20250918012018.s3-website-us-east-1.amazonaws.com' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept, Authorization' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
        }
    }
}
EOF

# Test and restart nginx
sudo nginx -t && sudo systemctl restart nginx
echo "✅ Nginx configured and restarted!"