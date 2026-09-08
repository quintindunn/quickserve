#!/bin/bash

set -e

USERNAME="quickserve"
GROUPNAME="quickserve"
ROOT="/opt/quickserve"

if ! getent group "$GROUPNAME" > /dev/null; then
    echo "Creating group: $GROUPNAME"
    groupadd --system "$GROUPNAME"
fi

if ! id "$USERNAME" > /dev/null 2>&1; then
    echo "Creating user: $USERNAME"
    useradd \
        --system \
        --gid "$GROUPNAME" \
        --no-create-home \
        --shell /usr/sbin/nologin \
        "$USERNAME"
fi

echo "Setting up $ROOT"

mkdir -p "$ROOT"
chown -R "$USERNAME:$GROUPNAME" "$ROOT"
chmod 755 "$ROOT"

echo "QuickServe user setup complete."