#!/bin/bash

#Test students import
../helper/create-students-import.sh > /tmp/schüler.csv
crx_import_user_list.py --input /tmp/schüler.csv --role students --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs

#Make some tests:
if [ ! -d /home/groups/5A ]; then
	echo  "Class dir was not created"
fi
#TODO make more tests

#Test teachers import
../helper/create-teachers-import.sh > /tmp/teachers.csv
crx_import_user_list.py --input /tmp/teachers.csv --role teachers --full --appendBirthdayToPassword --appendClassToPassword --cleanClassDirs

#Create AdHocLan Rooms for classes
/usr/share/cranix/tools/handle_class_adhoc_rooms.py

#Register some devices for the students
for user in $( /usr/sbin/crx_api.sh GET users/uidsByRole/students )
do
	MAC=$( ../helper/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
	MAC=$( ../helper/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
done
