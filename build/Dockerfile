FROM alpine:latest

RUN apk add --no-cache openssh-client rsync util-linux bash tzdata jq python3

COPY build/entrypoint.sh /entrypoint.sh
COPY src /src

RUN chmod +x /entrypoint.sh /src/sync_script.sh /src/web_server.py

VOLUME /data

CMD ["/entrypoint.sh"]