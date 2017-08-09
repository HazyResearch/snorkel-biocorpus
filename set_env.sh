export APPHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SNORKELHOME="$APPHOME/snorkel"
export DDBIOLIBHOME="$APPHOME/ddbiolib"

echo "app home directory: $APPHOME"
echo "ddbiolib home directory: $DDBIOLIBHOME"
echo "snorkel home directory: $SNORKELHOME"

export PYTHONPATH="$PYTHONPATH:$APPHOME:$SNORKELHOME:$DDBIOLIBHOME:$SNORKELHOME/treedlib"
export PATH="$PATH:$APPHOME:$SNORKELHOME:$DDBIOLIBHOME:$SNORKELHOME/treedlib"
echo "$PYTHONPATH"
echo "Environment variables set!"
