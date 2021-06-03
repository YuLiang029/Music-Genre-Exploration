#!/bin/bash

if test -f ".env"; then
  export $(cat .env | xargs)
fi

if [ -z "$YU_POSTGRESQL_PASSWORD"]; then "You forgot to set POSTGRESQL_PASSWORD variable!" && exit 1; fi
if [ -z "$YU_SPOTIFY_CLIENT_ID"]; then "You forgot to set YU_SPOTIFY_CLIENT_ID variable!" && exit 1; fi
if [ -z "$YU_SPOTIFY_CLIENT_SECRET"]; then "You forgot to set YU_SPOTIFY_CLIENT_SECRET variable!" && exit 1; fi
