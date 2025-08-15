#!/bin/bash

COMPOSE_FILE="compose-prod.yaml"
docker compose -f $COMPOSE_FILE down
docker compose -f $COMPOSE_FILE up --force-recreate --build -d