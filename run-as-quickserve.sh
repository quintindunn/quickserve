#!/bin/bash

clear

exec sudo -u quickserve \
    ~/PycharmProjects/QuickServe/.venv/bin/python "$@"
