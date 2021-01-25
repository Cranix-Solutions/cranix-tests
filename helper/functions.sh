# (C) 2021 Peter Varkoly <pvarkoly@cephalix.eu>
# Helper functions for testing the CRANIX-Server

function check_result {
	CODE=$( echo $1 | jq '.code' )
	MESS=$( echo $1 | jq '.value' )
	echo "$CODE $MESS"
}
