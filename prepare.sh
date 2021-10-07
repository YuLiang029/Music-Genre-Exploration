#!/bin/bash

if test -f ".env"; then
  export $(cat .env | xargs)
fi

if [ -z "$POSTGRESQL_PASSWORD" ]; then "You forgot to set POSTGRESQL_PASSWORD variable!" && exit 1; fi
if [ -z "$SPOTIFY_CLIENT_ID" ]; then "You forgot to set SPOTIFY_CLIENT_ID variable!" && exit 1; fi
if [ -z "$SPOTIFY_CLIENT_SECRET" ]; then "You forgot to set $SPOTIFY_CLIENT_SECRET variable!" && exit 1; fi