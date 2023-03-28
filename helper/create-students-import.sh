#!/bin/bash
startDate=$( date +%s -d "now - 7 years" )
if [ "$1" == "nextyear" ]; then
	startDate=$( date +%s -d "now - 6 years" )
fi
year=31536000
week=604800
if [ -z "$CLASS_COUNT" ]; then
        export CLASS_COUNT=4
fi
if [ -z "$STUDENT_COUNT" ]; then
        export STUDENT_COUNT=10
fi
echo "Nachname;Vorname;Geburtstag;Klasse"
for ((c1=1; c1<=${CLASS_COUNT}; c1++))
do
	BD=$startDate
	for c2 in {a..c}
	do
		YEAR=$( date +%Y -d @${BD} )
		class=${c1}${c2}
		for ((u=1; u<=${STUDENT_COUNT}; u++))
		do
			BD=$((BD+week))
			birthDay=$( date +%Y-%m-%d -d @${BD} )
			givenName=$( date  +%B%U -d @${BD} )
			echo "$YEAR;$givenName;$birthDay;$class"
		done
	done
	startDate=$((startDate-year))
done
