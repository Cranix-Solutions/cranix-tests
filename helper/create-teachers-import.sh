#!/bin/bash
startDate=$( date +%s -d "now - 25 years" )
year=31536000
week=604800
BD=$((startDate+3*week))
echo "Nachname;Vorname;Geburtstag;Klasse"
for c1 in {1..20}
do
	YEAR=$( date +%Y -d @${BD} )
	birthDay=$( date +%Y-%m-%d -d @${BD} )
	givenName=$( date  +%B%U -d @${BD} )
	echo "$YEAR;$givenName;$birthDay;all"
	BD=$((BD-year+c1*week))
done
