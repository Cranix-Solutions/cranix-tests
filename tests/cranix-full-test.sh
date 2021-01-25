#!/bin/bash

source /etc/sysconfig/cranix
export TEST_BASE="/usr/share/cranix/tests"
export TEST_BIN="${TEST_BASE}/bin"
export TEST_HELPER="${TEST_BASE}/helper"
export NETWORK="${CRANIX_NETWORK}/${CRANIX_NETMASK}"
export TESTMP=$( mktemp -d /tmp/cranix-test-XXXXX )

for i in $( find ${TEST_BIN}/ -mindepth 1 -maxdepth 1 | sort )
do
	. $i
done

