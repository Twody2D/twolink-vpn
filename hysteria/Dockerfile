FROM alpine:3.20 AS downloader

RUN apk add --no-cache curl

ARG HYSTERIA_VERSION=app/v2.12.2
ARG HYSTERIA_SHA256=6493dfffd55b5883f64c76c63880ecc32988f0c568c9ca9014907877b4d55f94

RUN curl -fsSL -o /hysteria \
      "https://github.com/HyNetworks/hysteria/releases/download/${HYSTERIA_VERSION}/hysteria-linux-amd64" \
    && echo "${HYSTERIA_SHA256}  /hysteria" | sha256sum -c - \
    && chmod +x /hysteria

FROM alpine:3.20

RUN apk add --no-cache ca-certificates gettext openssl && \
    addgroup -S hysteria && adduser -S -G hysteria hysteria

COPY --from=downloader /hysteria /usr/local/bin/hysteria

COPY config/config.template.yaml /etc/hysteria/config.template.yaml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
    mkdir -p /etc/hysteria/generated /etc/hysteria/tls && \
    chown -R hysteria:hysteria /etc/hysteria

USER hysteria

ENTRYPOINT ["/entrypoint.sh"]
