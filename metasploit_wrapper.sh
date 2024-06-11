#!/bin/bash

# Script para ejecutar comandos en el contenedor Metasploit
COMMAND=$1
TIMEOUT=$2

# Ejecuta el comando en el contenedor Metasploit
docker exec metasploit_c2 bash -c "$COMMAND"

# Espera el tiempo especificado
sleep $((TIMEOUT / 1000000))

