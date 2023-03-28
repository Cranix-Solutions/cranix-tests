#!/bin/bash
startDate=$( date +%s -d "now - 25 years" )
year=31536000
week=604800
BD=$((startDate+3*week))
if [ -z "$TEACHER_COUNT" ]; then
        export TEACHER_COUNT=15
fi

echo "Nachname;Vorname;Geburtstag;Klasse"
for ((u=1; u<=${TEACHER_COUNT}; u++))
do
	YEAR=$( date +%Y -d @${BD} )
	birthDay=$( date +%Y-%m-%d -d @${BD} )
	givenName=$( date  +%B%U -d @${BD} )
	echo "$YEAR;$givenName;$birthDay;all"
	BD=$((BD-year+c1*week))
done
