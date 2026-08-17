#!/bin/sh
set -eu

required_vars="XRAY_VLESS_PORT XRAY_SS_PORT XRAY_API_PORT REALITY_DEST REALITY_SERVER_NAMES REALITY_PRIVATE_KEY REALITY_SHORT_ID SHADOWSOCKS_METHOD SHADOWSOCKS_PASSWORD"
for var in $required_vars; do
  eval "val=\${$var:-}"
  if [ -z "$val" ]; then
    echo "ERROR: required environment variable $var is not set" >&2
    exit 1
  fi
done

# Turn comma-separated REALITY_SERVER_NAMES into a JSON array for the template.
export REALITY_SERVER_NAMES_JSON=$(printf '%s' "$REALITY_SERVER_NAMES" | awk -F',' '{
  printf "["
  for (i = 1; i <= NF; i++) {
    gsub(/^ +| +$/, "", $i)
    printf "%s\"%s\"", (i > 1 ? "," : ""), $i
  }
  printf "]"
}')

envsubst < /etc/xray/config.template.json > /etc/xray/generated/config.json

exec /usr/local/bin/xray run -c /etc/xray/generated/config.json
