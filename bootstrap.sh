#!/bin/bash
# Should we check for Python or is that assumed??

# Define the help function
function show_help {
	echo "Usage: insights-client [options]"
	echo ""
	echo "Options:"
	echo -e "-h\t HALP!"
	echo -e "-d\t Run in development mode, this uses the LOCAL EGG source instead of reaching out to the mothership."
	echo -e "-o\t Run in offline mode, meaning DO NOT update the egg, or hatch a new egg, simply run whatever is currently installed."
	echo -e "-v\t Get the version."
	exit 0;
}

# Define the version function
function show_version {
	echo "Insights Client Version X.X.X"
	exit 0;
}

# Get some development options
OPTIND=1
DEVMODE=0
OFFLINE=0
while getopts "dhvo" opt; do
	case "$opt" in
	h) show_help ;;
	v) show_version ;;
	d) DEVMODE=1 ;;
	o) OFFLINE=1 ;;
	esac
done
shift $((OPTIND-1))
[ "$1" = "--" ] && shift

# TODO: Maybe implement a basic verbose flag in here somewhere
# Verbose stuff
echo "Running Insights Client."

# TODO: Need to implement some offline logic in here somewhere
# TODO: Need to implement dev mode logic in here somewhere

# Download the new Client Eggo
if [ $OFFLINE == 0 ] && [ $DEVMODE == 0 ]; then
	echo "Obtaining Insights Client"
	EGG_CURL=$(curl --insecure --write-out %{http_code} --silent --output uploader.json https://cert-api.access.redhat.com/r/insights/static/insights-client.egg)
	echo "Client retrieval response "$EGG_CURL
	if [ $EGG_CURL != 200 ]; then echo "Egg retrieval failed."; exit 1; fi;
	if [ $EGG_CURL == 200 ]; then echo "Egg retrieval success."; fi;
elif [ $OFFLINE == 1 ] && [ $DEVMODE == 1 ]; then
	echo "Not retrieving new Egg, running in OFFLINE and DEVMODE."
elif [ $OFFLINE == 1 ]; then
	echo "Not retrieving new Egg, running in OFFLINE mode."
elif [ $DEVMODE == 1 ]; then
	echo "Not retrieving new Egg, running in DEVMODE."
fi


# Verify the eggo
EGG_VERIFICATION=$(gpg --verify redhat.gpg insights-client.egg)

# Hatch the egg if it checks out
if [ $EGG_VERIFICATION == 0 ]; then
	python insights-client.egg;
fi

# Bail if it doesn't check out
if [ $EGG_VERIFICATION > 1 ]; then
	echo "Egg verification failed.";
	exit 1;
fi