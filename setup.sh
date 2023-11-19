#!/usr/bin/env bash
set -euo pipefail

if [ $# -gt 0 ]; then
	if [ "$1" == "update" ]; then
        echo -e "Running Update"
		eval "./server.sh" pull
		eval "./server.sh" stop
		eval "./server.sh" build
	elif [ "$1" == "recreate" ]; then
        echo -e "Running Recreate"
		eval "./server.sh" up -d --force-recreate
	else
        echo -e "Running Initailizing Server"
		eval "./server.sh" "$@"
	fi
fi
