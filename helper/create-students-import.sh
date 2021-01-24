#!/bin/bash
startDate=$( date +%s -d "now - 7 years" )
if [ "$1" == "nextyear" ]; then
	startDate=$( date +%s -d "now - 6 years" )
fi
year=31536000
week=604800
echo "Nachname;Vorname;Geburtstag;Klasse"
for c1 in {1..8}
do
	BD=$startDate
	for c2 in {a..c}
	do
		YEAR=$( date +%Y -d @${BD} )
		class=${c1}${c2}
		for u in {1..15}
		do
			BD=$((BD+week))
			birthDay=$( date +%Y-%m-%d -d @${BD} )
			givenName=$( date  +%B%U -d @${BD} )
			echo "$YEAR;$givenName;$birthDay;$class"
		done
	done
	startDate=$((startDate-year))
done
