#
# Copyright (C) 2021 Peter Varkoly <pvarkoly@cephalix.eu> Nürnberg, Germany.  All rights reserved.
#
DESTDIR         = /
SHARE           = $(DESTDIR)/usr/share/cranix/tests
SYSTEMD         = $(DESTDIR)/usr/lib/systemd/system
APACHECONF      = $(DESTDIR)/etc/apache2/conf.d
TOPACKAGE       = bin datas helper tests datas Makefile README.md webapp QA-TESTPLAN.md QA-TESTPLAN.de.md
HERE            = $(shell pwd)
REPO            = /data1/OSC/home:pvarkoly:CRANIX
PACKAGE         = cranix-tests

install:
	mkdir -p $(SHARE)/{bin,datas,helper,tests,webapp/static}
	install -m 755   tests/*   $(SHARE)/tests/
	install -m 755   bin/*     $(SHARE)/bin/
	install -m 644   datas/*   $(SHARE)/datas/
	install -m 755   helper/*  $(SHARE)/helper/
	install -m 644   QA-TESTPLAN.md QA-TESTPLAN.de.md $(SHARE)/
	install -m 755   webapp/server.py webapp/plan_parser.py $(SHARE)/webapp/
	install -m 644   webapp/index.html $(SHARE)/webapp/
	install -m 644   webapp/static/* $(SHARE)/webapp/static/
	install -d $(SYSTEMD) $(APACHECONF)
	install -m 644   webapp/cranix-testcollector.service $(SYSTEMD)/
	install -m 644   webapp/apache-cranix-testcollector.conf.example $(APACHECONF)/

dist:
	xterm -e git log --raw  &
	if [ -e $(PACKAGE) ] ;  then rm -rf $(PACKAGE) ; fi
	mkdir $(PACKAGE)
	for i in $(TOPACKAGE); do \
	    cp -rp $$i $(PACKAGE); \
	done
	find $(PACKAGE) -type f > files;
	tar jcpf $(PACKAGE).tar.bz2 -T files;
	rm files
	rm -rf $(PACKAGE)
	if [ -d $(REPO)/$(PACKAGE) ] ; then \
	   cd $(REPO)/$(PACKAGE); osc up; cd $(HERE);\
	   mv $(PACKAGE).tar.bz2 $(REPO)/$(PACKAGE); \
	   cd $(REPO)/$(PACKAGE); \
	   osc vc; \
	   osc ci -m "New Build Version"; \
	fi

