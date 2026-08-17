#!/bin/sh
set -eu

CERT_DIR=/etc/node-agent/tls

if [ ! -f "$CERT_DIR/cert.pem" ]; then
  openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
    -days 3650 -nodes -subj "/CN=twolink-node-agent"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile "$CERT_DIR/key.pem" --ssl-certfile "$CERT_DIR/cert.pem"
