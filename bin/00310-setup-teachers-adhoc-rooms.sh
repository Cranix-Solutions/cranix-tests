#!/bin/bash
source ${TEST_HELPER}/functions.sh
#
echo '{"name":"lehrer-wlan","description":"AdHoc Raum Lehrer","roomType":"AdHocAccess","roomControl":"no","network":"'${NETWORK}'","hwconfId":3,"devCount":256,"studentsOnly":false,"groupIds":[2],"devicesProUser":4}' > $TESTMP/00310-setup-teachers-adhoc-rooms.json

check_result "$( /usr/sbin/crx_api_post_file.sh adhocrooms/add $TESTMP/00310-setup-teachers-adhoc-rooms.json )"

#Register some devices for the students
for user in $( /usr/sbin/crx_api.sh GET users/uidsByRole/teachers )
do
	MAC=$( ${TEST_HELPER}/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
	MAC=$( ${TEST_HELPER}/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
	MAC=$( ${TEST_HELPER}/create-random-mac.sh )
	curl -s -X PUT "http://localhost:9080/api/selfmanagement/addDeviceToUser/$MAC/$user"
done

