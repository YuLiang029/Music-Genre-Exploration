#!/bin/bash

if test -f ".env"; then
  export $(cat .env | xargs)
fi

if [ -z "$POSTGRESQL_PASSWORD"]; then "You forgot to set POSTGRESQL_PASSWORD variable!" && exit 1; fi
