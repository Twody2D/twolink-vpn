#!/bin/sh
set -eu

required_vars="HYSTERIA_PORT HYSTERIA_OBFS_PASSWORD HYSTERIA_AUTH_URL"
for var in $required_vars; do
  eval "val=\${$var:-}"
  if [ -z "$val" ]; then
    echo "ERROR: required environment variable $var is not set" >&2
    exit 1
  fi
done

# Certificate lives on a named volume and is generated only once: client
# subscription links pin its SHA-256 fingerprint, so regenerating it on every
# restart would silently break every link already handed out.
CERT_DIR=/etc/hysteria/tls
if [ ! -f "$CERT_DIR/cert.pem" ]; then
  openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
    -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
    -days 3650 -nodes -subj "/CN=twolink"
fi

FINGERPRINT=$(openssl x509 -in "$CERT_DIR/cert.pem" -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')
echo "Certificate SHA-256 fingerprint (pinSHA256): $FINGERPRINT"

envsubst < /etc/hysteria/config.template.yaml > /etc/hysteria/generated/config.yaml

exec /usr/local/bin/hysteria server -c /etc/hysteria/generated/config.yaml
