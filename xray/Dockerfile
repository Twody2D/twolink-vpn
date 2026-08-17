FROM ghcr.io/xtls/xray-core:latest AS xray-bin

FROM alpine:3.20

RUN apk add --no-cache ca-certificates gettext && \
    addgroup -S xray && adduser -S -G xray xray

COPY --from=xray-bin /usr/local/bin/xray /usr/local/bin/xray

COPY config/config.template.json /etc/xray/config.template.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
    mkdir -p /etc/xray/generated && \
    chown -R xray:xray /etc/xray

USER xray

ENTRYPOINT ["/entrypoint.sh"]
