#!/bin/bash

#Test students import
${TEST_HELPER}/create-students-import.sh > /tmp/schüler.csv
crx_import_user_list.py --input /tmp/schüler.csv --role students --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs

#Make some tests:
if [ ! -d /home/groups/5A ]; then
	echo  "Class dir was not created"
fi
#TODO make more tests

#Test teachers import
${TEST_HELPER}/create-teachers-import.sh > /tmp/teachers.csv
crx_import_user_list.py --input /tmp/teachers.csv --role teachers --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs

