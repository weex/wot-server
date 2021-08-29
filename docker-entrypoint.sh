#!/bin/sh

for f in docker-entrypoint.d/*; do
    case "$f" in
        *.sh)     echo "$0: running $f"; . "$f" ;;
        *.sql)    echo "$0: running $f"; psql -h localhost wot-server < "$f"; echo ;;
        *.sql.gz) echo "$0: running $f"; gunzip -c "$f" | "${psql[@]}"; echo ;;
        *)        echo "$0: ignoring $f" ;;
    esac
    echo
done
