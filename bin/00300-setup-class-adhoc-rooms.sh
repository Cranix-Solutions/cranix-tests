#!/bin/bash

#
sed -i 's/CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES=*/CRANIX_MAINTAIN_ADHOC_ROOM_FOR_CLASSES="yes"/' /etc/sysconfig/cranix
sed -i 's/CRANIX_CLASS_ADHOC_DEVICE_PRO_USER=*/CRANIX_CLASS_ADHOC_DEVICE_PRO_USER="2"/' /etc/sysconfig/cranix
sed -i 's/CRANIX_CLASS_ADHOC_DEVICE_COUNT=*/CRANIX_CLASS_ADHOC_DEVICE_COUNT="32"/' /etc/sysconfig/cranix

#Create AdHocLan Rooms for classes
/usr/share/cranix/tools/handle_class_adhoc_rooms.py

#Register some devices for the students
for user in $( /usr/sbin/crx_api.sh GET users/uidsByRole/students )
do
	MAC=$( ${TEST_HELPER}/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
	MAC=$( ${TEST_HELPER}/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
done


