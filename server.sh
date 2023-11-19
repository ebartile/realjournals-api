#!/usr/bin/env bash
set -euo pipefail

UNAMEOUT="$(uname -s)"

WHITE='\033[1;37m'
NC='\033[0m'

echo "We are running the application on $UNAMEOUT"

# Verify operating system is supported...
case "${UNAMEOUT}" in
Linux*) MACHINE=linux ;;
Darwin*) MACHINE=mac ;;
*) MACHINE="UNKNOWN" ;;
esac

if [ "$MACHINE" == "UNKNOWN" ]; then
	echo "Unsupported operating system [$(uname -s)]. Server supports macOS, Linux, and Windows (WSL2)." >&2 && exit 1
fi

if [[ $EUID -eq 0 ]]; then
	echo -e "You cannot start Server as root." >&2 && exit 1
fi

echo -e "Setting environment variables" 

# Define environment variables...
export API_SERVICE=${API_SERVICE:-"api"}
export HOST_API_UID=${HOST_API_UID:-$(id -u "realjournals")}
export API_USER=${HOST_API_UID}
export REDIS_VERSION=${REDIS_VERSION:-"6"}

if [ "$MACHINE" == "linux" ]; then
	export SEDCMD="sed -i"
elif [ "$MACHINE" == "mac" ]; then
	export SEDCMD="sed -i .bak"
fi

echo -e "Ensuring that Docker is running..." 
# Ensure that Docker is running...
if ! docker info >/dev/null 2>&1; then	
	echo -e "Docker is not running. Installing docker" >&2 && exit 1
fi

echo -e "Setting up letsencrypt..." 
# Setting up letsencrypt
mkdir -p "${HOME}"/www/certbot
mkdir -p "${HOME}"/lib/letsencrypt
mkdir -p "${HOME}"/log/letsencrypt
mkdir -p "${HOME}"/letsencrypt

if [ ! -f "${HOME}"/letsencrypt/ssl-dhparams.pem ]; then
	openssl dhparam -out "${HOME}"/letsencrypt/ssl-dhparams.pem 2048
fi

echo -e "Creating external nginx network..." 
# Create external nginx network
if ! docker network inspect nginx-proxy >/dev/null 2>&1; then
	docker network create nginx-proxy
fi

function initialize_env() {
	set -euo pipefail

	echo -e "Initializing Env" 
	
	if [ ! -f ./api/.env ]; then
		cp ./api/.env.example ./api/.env

		echo -e "env initialized"
	else
		echo -e "env file exists"
	fi
}

function initialize_project() {
	set -euo pipefail

	DEFAULT_ALIAS=${PWD##*/}

	initialize_env

	echo -e "Setting up docker image server."


	echo -e "Server installed successfully."
}

if [ $# -gt 0 ]; then
	# Initialize project
	if [ "$1" == "init-project" ]; then
		initialize_project && exit 0

	# Initialize .env
	elif [ "$1" == "init-env" ]; then
		initialize_env && exit 0

	fi
fi

function server_is_not_running() {
	echo -e "Server is not running." >&2 && exit 1
}

if [ $# -gt 0 ]; then
	# Source environment files
	if [ -f ./api/.env ]; then
		source ./api/.env
	else
		echo -e "${WHITE}.env file does not exists:${NC}" >&2
		echo -e "Run 'init' command first." >&2 && exit 1
	fi

	if [ "$APP_ENV" == "production" ] && [ "$APP_DEBUG" == "true" ]; then
		echo "You need to set APP_DEBUG=false in production" >&2 && exit 1
	fi

	if [[ $API_HOST ]]; then
		export API_DOMAIN=${API_HOST}
	else
		echo "The value of API_HOST is invalid." >&2 && exit 1
	fi

	function set_nginx_ssl_directive() {
		CERTIFICATE_API_DIR="${HOME}/letsencrypt/live/${API_DOMAIN}"

		export NGINX_HTTP_PORT="80"
		export NGINX_HTTPS_PORT="443"

		if  [ -f "${CERTIFICATE_API_DIR}/fullchain.pem" ] && [ -f "${CERTIFICATE_API_DIR}/privkey.pem" ]; then
			export NGINX_DEFAULT_API_CONFIG="/etc/nginx/conf.d/api.ssl"
		else
			export NGINX_DEFAULT_API_CONFIG="/etc/nginx/conf.d/api"
		fi
	}

	set_nginx_ssl_directive

	CERTBOT="docker run -it --rm -u $(id -u):$(id -g) \
	-v ${HOME}/letsencrypt:/etc/letsencrypt \
	-v ${HOME}/lib/letsencrypt:/var/lib/letsencrypt \
	-v ${HOME}/log/letsencrypt:/var/log/letsencrypt \
	-v ${HOME}/www/certbot:/var/www/certbot \
	certbot/certbot"

	# Determine if Server is currently up...
	if docker-compose --env-file ./api/.env ps 2>/dev/null | grep -q 'Exit'; then
		EXEC="no"
	elif [ -n "$(docker-compose --env-file ./api/.env ps -q 2>/dev/null)" ]; then
		EXEC="yes"
	else
		EXEC="no"
	fi

	# Run ssl to secure container...
	if [ "$1" == "ssl" ]; then
		shift 1

		if [ -z "$CERTBOT_EMAIL" ]; then
			echo -e "Set CERTBOT_EMAIL to proceed." >&2 && exit 1
		fi

		if [ "$EXEC" == "yes" ]; then
			eval "$CERTBOT" certonly --webroot --webroot-path=/var/www/certbot \
				--email "$CERTBOT_EMAIL" --agree-tos --no-eff-email --force-renewal \
				-d "$API_DOMAIN"

			set_nginx_ssl_directive

			docker-compose --env-file ./api/.env up -d
		else
			server_is_not_running
		fi

	# Renew ssl to secure container...
	elif [ "$1" == "ssl-renew" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			eval "$CERTBOT" renew && docker-compose --env-file ./api/.env restart
		else
			server_is_not_running
		fi

	# Disable 'down' and 'rm' commands
	elif [ "$1" == "down" ] || [ "$1" == "rm" ]; then
		echo -e "The command is disabled." >&2 && exit 1

	# Proxy python commands to the "python" binary on the application container...
	elif [ "$1" == "python" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				"$API_SERVICE" \
				--env-file ./api/.env \
				python "$@"
		else
			server_is_not_running
		fi

	# Proxy pip commands to the "pip" binary on the application container...
	elif [ "$1" == "pip" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				"$API_SERVICE" \
				--env-file ./api/.env \
				pip "$@"
		else
			server_is_not_running
		fi

	# Proxy manage.py commands to the "manage.py" binary on the application container...
	elif [ "$1" == "manage.py" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				"$API_SERVICE" \
				--env-file ./api/.env \
				python manage.py "$@"
		else
			server_is_not_running
		fi

	# Proxy the "test" command to the "python manage.py test" Artisan command...
	elif [ "$1" == "test" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				"$API_SERVICE" \
				--env-file ./api/.env \
				python manage.py test "$@"
		else
			server_is_not_running
		fi
	# Initiate a Redis CLI terminal session within the "redis" container...
	elif [ "$1" == "redis" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			
			docker-compose exec \
				-u "$API_USER" \
				--env-file ./api/.env \
				redis redis-cli "$@"
		else
			server_is_not_running
		fi

	elif [ "$1" == "exec-app-no-tty" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				-T "$API_SERVICE" \
				--env-file ./api/.env \
				"$@"
		else
			server_is_not_running
		fi

	# Initiate a Postgres CLI terminal session within the "Postgres" container...
	elif [ "$1" == "psql" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				postgres_db1 psql \
				--env-file ./api/.env \
				-U "$DB_USER" \
				-d "$DB_NAME" -c "$@"
		else
			server_is_not_running
		fi

	# Initiate a Bash shell within the application container...
	elif [ "$1" == "shell" ] || [ "$1" == "bash" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				-u "$API_USER" \
				"$API_SERVICE" \
				--env-file ./api/.env \
				bash
		else
			server_is_not_running
		fi

	# Initiate a root user Bash shell within the application container...
	elif [ "$1" == "root-shell" ]; then
		shift 1

		if [ "$EXEC" == "yes" ]; then
			docker-compose exec \
				"$API_SERVICE" \
				--env-file ./api/.env \
				bash
		else
			server_is_not_running
		fi

	# Redirect the default 'start' command to 'up'...
	elif [ "$1" == "start" ]; then
		shift 1

		docker-compose --env-file ./api/.env up -d

	# Pass unknown commands to the "docker-compose"...
	else
		docker-compose --env-file ./api/.env "$@"
	fi
else
	docker-compose --env-file ./api/.env ps
fi

