# Copyright 2013 Telefonica Investigacion y Desarrollo, S.A.U
#
# This file is part of Orion Context Broker.
#
# Orion Context Broker is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Orion Context Broker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Orion Context Broker. If not, see http://www.gnu.org/licenses/.
#
# For those usages not covered by this license please contact with
# fermin at tid dot es

%define name contextBroker
%define owner orion 

# Don't byte compile python code
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Summary:   Orion Context Broker
Name:      %{name}
Version:   %{broker_version}
Release:   %{broker_release}
License:   AGPLv3
Group:     Applications/Engineering
Vendor:     Telefónica I+D
Packager:   Fermín Galán <fermin@tid.es>
URL:        http://catalogue.fi-ware.eu/enablers/publishsubscribe-context-broker-orion-context-broker
Source:     %{name}-%{broker_version}.tar.gz
BuildRoot: /var/tmp/%{name}-buildroot
Requires:  libstdc++, boost-thread, boost-filesystem, libmicrohttpd, logrotate
Buildrequires: gcc, cmake, gcc-c++, libmicrohttpd-devel, boost-devel
Requires(pre): shadow-utils

%description
The Orion Context Broker is an implementation of NGSI9 and NGSI10 interfaces. 
Using these interfaces, clients can do several operations:
* Register context producer applications, e.g. a temperature sensor within a room.
* Update context information, e.g. send updates of temperature.
* Being notified when changes on context information take place (e.g. the
  temperature has changed) or with a given frecuency (e.g. get the temperature
  each minute).
* Query context information. The Orion Context Broker stores context information
  updated from applications, so queries are resolved based on that information.

%prep
if [ -d $RPM_BUILD_ROOT/usr ]; then
   rm -rf $RPM_BUILD_ROOT
fi

%setup

%pre
getent group %{owner} >/dev/null || groupadd -r %{owner}
getent passwd %{owner} >/dev/null || useradd -r -g %{owner} -m -d /opt/orion -s /bin/bash -c 'Orion account' %{owner}
# Backup previous sysconfig file (if any)
DATE=$(date "+%Y-%m-%d")
if [ -f "/etc/sysconfig/%{name}" ]; then
   cp /etc/sysconfig/%{name} /etc/sysconfig/%{name}.orig-$DATE
   chown %{owner}:%{owner} /etc/sysconfig/%{name}.orig-$DATE
fi
exit 0

%post
DATE=$(date "+%Y-%m-%d")
/sbin/chkconfig --add %{name}
mkdir -p /var/log/%{name}
chown -R %{owner}:%{owner} /var/log/%{name}
# Secure the configuration file to prevent un-authorized access
chown %{owner}:%{owner} /etc/sysconfig/%{name}
chmod 600 /etc/sysconfig/%{name}
cat <<EOMSG
contextBroker requires additional configuration before the service can be
started. Edit '/etc/sysconfig/%{name}' to provide the needed database
configuration.

Note that if you have a previously existing '/etc/sysconfig/%{name}' it
has been renamed to /etc/sysconfig/%{name}.orig-$DATE.

After configuring /etc/sysconfig/%{name} execute 'chkconfig %{name} on' to
enable %{name} after a reboot.
EOMSG

%clean
rm -rf $RPM_BUILD_ROOT
rm -rf %{_builddir}

%build
#FIXME There is an open issue with "make release" malfunction. Until get fixed, we will build in debug mode
#make release DESTDIR=$RPM_BUILD_ROOT BUILD_ARCH=%{build_arch}
make debug DESTDIR=$RPM_BUILD_ROOT BUILD_ARCH=%{build_arch}

%install
#FIXME There is an open issue with "make release" malfunction. Until get fixed, we will build in debug mode
#make install DESTDIR=$RPM_BUILD_ROOT
make install_debug DESTDIR=$RPM_BUILD_ROOT
cp -R %{_sourcedir}/etc $RPM_BUILD_ROOT

# rpmbuild seems to do the strip step automatically. However, this would fail after chmod, so we "manually" do
# it as part of our install script
strip $RPM_BUILD_ROOT/usr/bin/contextBroker
chmod 555 $RPM_BUILD_ROOT/usr/bin/contextBroker
mkdir -p $RPM_BUILD_ROOT/var/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/init.d
mkdir -p $RPM_BUILD_ROOT/etc/profile.d
mkdir -p $RPM_BUILD_ROOT/usr/share/contextBroker/tests
mkdir -p $RPM_BUILD_ROOT/usr/share/doc/contextBroker
cp -r test/functionalTest/cases $RPM_BUILD_ROOT/usr/share/contextBroker/tests
rm $RPM_BUILD_ROOT/usr/share/contextBroker/tests/cases/*.DISABLED $RPM_BUILD_ROOT/usr/share/contextBroker/tests/cases/CMakeLists.txt
cp LICENSE $RPM_BUILD_ROOT/usr/share/doc/contextBroker
cp scripts/testEnv.sh test/functionalTest/testHarness.sh test/functionalTest/testDiff.py test/functionalTest/harnessFunctions.sh $RPM_BUILD_ROOT/usr/share/contextBroker/tests
cp scripts/accumulator-server.py $RPM_BUILD_ROOT/usr/share/contextBroker/tests 
cp scripts/managedb/garbage-collector.py $RPM_BUILD_ROOT/usr/share/contextBroker
cp scripts/managedb/lastest-updates.py $RPM_BUILD_ROOT/usr/share/contextBroker
cp etc/init.d/contextBroker.centos $RPM_BUILD_ROOT/etc/init.d/%{name}
chmod 755 $RPM_BUILD_ROOT/etc/init.d/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
cp etc/config/contextBroker $RPM_BUILD_ROOT/etc/sysconfig/%{name}

echo "%%defattr(-, root, root, - )" > MANIFEST
(cd %{buildroot}; find . -type f -or -type l | sed -e s/^.// -e /^$/d) >>MANIFEST

grep -v "tests" MANIFEST > MANIFEST.broker
grep "tests" MANIFEST > MANIFEST.broker-tests

%files -f MANIFEST.broker

%changelog

%package tests
Requires: %{name}, python, python-flask, python-jinja2, nc, curl, libxml2, mongo-10gen 
Summary: Test suite for %{name}
%description tests
Test suite for %{name}

%files tests -f MANIFEST.broker-tests

%package -n %{name}-fiware
Requires: %{name} = %{broker_version}-%{broker_release}, %{name}-tests = %{broker_version}-%{broker_release}
Summary: FI-WARE NGSI Broker - Telefónica I+D Implementation
Version: %{fiware_version}
Release: %{fiware_release}
%description -n %{name}-fiware
The Orion Context Broker is an implementation of the NGSI9 and NGSI10 interfaces. 
Using these interfaces, clients can do several operations:
* Register context producer applications, e.g. a temperature sensor within a room.
* Update context information, e.g. send updates of temperature.
* Being notified when changes on context information take place (e.g. the
  temperature has changed) or with a given frecuency (e.g. get the temperature
  each minute).
* Query context information. The Orion Context Broker stores context information
  updated from applications, so queries are resolved based on that information.

%files -n %{name}-fiware

%preun
/etc/init.d/%{name} stop
/sbin/chkconfig --del %{name}

%preun tests

%preun -n %{name}-fiware
/etc/init.d/%{name} stop
/sbin/chkconfig --del %{name}

%postun 
rm -rf  /usr/share/contextBroker
/usr/sbin/userdel -f %{owner}

%postun tests
rm -rf  /usr/share/contextBroker/tests

%postun -n %{name}-fiware
rm -rf  /usr/share/contextBroker
/usr/sbin/userdel -f %{owner}


%changelog
* Fri May 30 2014 Fermin Galan <fermin@tid.es> 0.13.0-1 (FIWARE-3.4.2-1)
- Add: Rush can now be used as relayer for the broker, using the option '-rush' (issue #251)
- Add: Custom metadata support (issue #252)
- Add: Multi-service/tenant support, using the option -multiservice (issue #322)
- Add: Generic URI parameters supported (issue #372)
- Add: Notification mime-type selected in URI parameter 'notifyFormat' (supported values: "XML" and "JSON") (issue #372)
- Fix: Raising error on updateContext with location metadata doesn't involve actual change of location attribute (issue #351)
- Fix: The functionality to change the Log configuration via REST had stopped working. Fixed.
- FIX: The Log configuration via REST used "/log/traceLevel", whereas the documentation states "/log/trace".
       Updated the broker to support both "/log/trace" and "/log/traceLevel"
- Fix: Changed the XML tags AttributeAssociationList and AttributeAssociation to start with lowercase 'a'. (issue #378)
- Fix: Concatenation of strings now done by the compiler (in numerous places). (issue #384)
- Fix: Passing all complex parameters by reference or pointer (issues #263 and #354)

* Wed Apr 30 2014 Fermin Galan <fermin@tid.es> 0.12.0-1 (FIWARE-3.4.1-1)
- Add:  The broker now supports https, see CLI options '-https', '-cert' and '-key'
- Add:  New command line option '--silent', to suppress all log messages except errors. (Issue #291)
- Fix:  All responses with StatusCode now have the 'reasonPhrase' in accordance with the 'code' (Issue 242).
- Fix:  Every Context Element gets its corresponding Context Element Response when processing updateContext operations
        (previous version was interrupted in the middle if the processing if one Context Element resulted in error).
- Fix:  Requests with unacceptable Content-Type (HTTP header) get a "415 Unsupported Media Type" and a descriptive payload 'orionError'.
        Requests with unsupported 'Accept' format (HTTP header) get a "406 Not Acceptable" and a descriptive payload 'orionError'.
        Requests with "both 415 and 406" get a "415 Unsupported Media Type" and a descriptive payload 'orionError' in XML. (Issue #48)
- Fix:  The broker now performs retries when connecting to mongodb at startup. (Issue #308)
- Fix:  Responses containing context attributes with *compound values* AND metadata is now correctly rendered (Issue #323).
- Fix:  Now it is possible to have 'not in use' as a valid context value.
- Fix:  The ISO8601 parser has been improved. (Issue #231)
- Fix:  An important bug in the log trace library has been fixed. This fix *may* solve 'strange errors' (Issue #313)
- Fix:  Fixed a bug about empty context attribute values, probably introduced when compound values were invented (release 0.11.0).
- Fix:  Fixed the bug for failing long requests (Issue #333)
- Fix:  Changed the string for associations from 'Include Assciations' to 'IncludeAssociations' (small part of issue #334)

* Wed Apr 09 2014 Fermin Galan <fermin@tid.es> 0.11.0-1 (FIWARE-3.3.3-1)
- Add: "geo" queries functionality.
- Add: attribute values can now be not only simple strings but compound expressions with vectors and key-maps
- Add: It is now possible to delete entities using updateContext DELETE with empty attributes list
- Fix: Fixed convenience operation "DELETE /ngsi10/contextEntities/{EntityID}" (partially fixes issue #225)
- Fix: The CLI options now coincide with the documentation.
- Fix: Introduced a second semaphore level as additional security measure to ensure all MongoDB driver invocations run in thread-safe mode.
- Fix: Convenience operations now correctly parse context values. (Bug #219)
- Add: It is now possible to update attribute values using a convenience operation without using metadatas.
- Fix: StatusCode is now correctly rendered in JSON when sent as a standalone message (partially fixes issue #225)
- Fix: Fixed a bug about incoming buffer pollution.
- Fix: Some unknown incoming URLs were not responded to. Now they are. (Bug #277)
- Fix: Now the operations GET, POST and PUT work properly with convenience operations over valueID's.
- Fix: JSON/XML Payload parsing that ended in parse error had a bug resulting in a possible memory leak.
- Fix: Convenience operation GET with non-existent valueIDs is now handled correctly.
- Fix: Stronger checking of XML/JSON payload request conformance: not only mandatory elements are checked,
       but also now a parse error is returned if the client tries to use an unrecognized element in any part of the payload.

* Wed Feb 26 2014 Fermin Galan <fermin@tid.es> 0.10.1-1 (FIWARE-3.3.2-1)
- Fix: concurrently bug in ONTIMEINTERVAL threads running with the same clock frecuency and phase
- Fix: some problems in the previous solution to issue #208

* Thu Feb 20 2014 Fermin Galan <fermin@tid.es> 0.10.0-1 (FIWARE-3.3.2-1)
- Added:  IPv6 support (By default, both IPv4 and IPv6 are activated - the new command line options '-ipv4' and '-ipv6' make the broker activate only one of them)
- Added:  JSON support for all implemented convenience operations
- Fixed:  Concurrency problem for JSON parser is solved
- Fixed:  Bug that prevented the use of UpdateContextRequest in JSON with DELETE as action (closes #224)
- Fixed:  Expiration times are now 64-bit integers (there was a previous problem with overflow) (closes #208)
- Fixed:  Bug that incorrectly allowed using an object within an object instead of an object in an array (closes #223)
- Fixed:  Fixed bug that displayed the tag "contextValue" instead of "value" in some instances for JSON rendering (closes 
#219)
- Fixed:  Removed subscriptionId from SubscribeContextAvailability
- Fixed:  XML tag names for scope rendering ('scopeType'/'scopeValue' instead of 'type'/'value')
- Fixed:  Changed "0" for "000000000000000000000000" in subscriptionId
- Fixed:  Removed some spaces from XML tags (E.g. 'verbose level' => 'verboseLevel')
- Fixed:  Stripped 'reference' of whitespace
- Fixed:  Added an empty contextAttributeList for ContextAttributeResponseVector inside IndividualContextEntityAttributes (/ngsi10/contextEntities/{EID}/attributes) as the XSD demands it
- Fixed:  Possible future error for JSON rendering of UpdateContextAvailabilitySubscriptionRequest
- Fixed:  The reasonPhrase in statusCode/errorCode and OrionError is now 100% tied to the 'code'
- Fixed:  OrionError now also with 'reasonPhrase' following 'code'

* Mon Jan 20 2014 Fermin Galan <fermin@tid.es> 0.9.1-1 (FIWARE-3.3.1-1)
- Added:  tracelevels for input/output for notifications and registrations forwarding
- Added:  creDate attribute now also for attributes in mongodb
- Fixed:  race-condition in HTTP client code, affecting mainly the sending of notifications (closes issue #13)
- Fixed:  modDate is now set for entities and attributes at creation time
- Fixed:  added the missing comma for the ContextRegistration vector at rendering registerContextRequest
- Fixed:  registrationId is now mandatory for registerContextResponse
- Fixed:  correct rendering of ContextRegistrationAttribute (its metadata    XML tag    was incorrect)
- Fixed:  duration no longer returned in response payloads if the incoming duration was invalid
- Fixed:  better RegisterProviderRequest validity check. This fix improves the error responses for ngsi9 convenience operations
- Fixed:  bug regarding the 'default' value of 'subscriptionId'. Before this PR, in the case of an undefined subscriptionId, the string 'No SubscriptionId' was used.
- Fixed:  orionError responses now correctly rendered (the top-level '{' and '}' were missing)

* Mon Dec 16 2013 Fermin Galan <fermin@tid.es> 0.9.0-1 (FIWARE-3.2.3-1)
- Complete JSON support for NGSI9/10 standard operations
- Decoupled NGSI9 and NGSI10 functionality
- Complete convenience operations support (XML payload in/out), except the ones related to attribute domains
- Much improved alignment with FI-WARE NGSI XSD in XML payloads
- Support for metadata ID attribute in queryContext, updateContext and equivalent convenience operations
- FIX avoid sending empty notifications with ONTIMEINTERVAL (issue #47)
- Tracelevels changes and cleanup
- Trace for incomplete payload and unsupported HTTP headers moved from warning log to tracelevel log
- ADD trace for output payload (under LmtRestReply tracelevel)
- Proper "User-Agent" and "Accept" headers in notifications sent
- FIX no Content-Type HTTP header for responses without payload
- FIX using HTTP 400 instead of 500 for payload parsing errors
- FIX proper payload per URL operation (issue #old72)
- FIX buffer overflow problems in logging subsystem

* Wed Oct 30 2013 Fermin Galan <fermin@tid.es> 0.8.1-1 (FIWARE-3.2.1-1)
- First version released as open source
- ADD lastest-updates.py script 
- ADD statistics as a REST service 
- ADD compilation information in REST version message
- REMOVE -reset from contextBroker invocation (too dangerous!)
- FIX licence text on --version, to use AGPLv3
- FIX problems with discoverContextAvailability when "type" and "id" is swapped in DB (spotted in Santander hackathon)
- FIX memory leaks
- FIX libmicrohttp-devel dependency not needed for runtime
- FIX crash with ONTIMEINTERVAL subscriptions (issue #9)
- Starting the work in JSON rendering, not yet finished

* Wed Oct 09 2013 Fermin Galan <fermin@tid.es> 0.8.0-1 (FIWARE-3.2.1-1)
- ADD libmicrohttpd-devel to RPM dependencies
- ADD entity creation timestamp in entities collection documents
- ADD entity and attributes modification timestamp in entities collection documents
- ADD notifications counter (count) in csubs and casubs collection documents
- ADD lastNotification timestamp in casubs collection documents
- ADD uptime to version message via REST
- Improve stability and performance
- Trace messages cleanup 

* Wed Oct 02 2013 Fermin Galan <fermin@tid.es> 0.7.3-1 (FIWARE-3.1.3-1)
- Fixed an important error in convenience function 'postIndividualContextEntityAttribute'
- Many fixes, many of them related with memory leaks and stability 
- Trace messages cleanup    
- Fix: empty Accept header right processing

* Fri Aug 30 2013 Fermin Galan <fermin@tid.es> 0.7.2-1 (FIWARE-3.1.2-1)
- FIX case insensitive HTTP processing

* Fri Aug 30 2013 Fermin Galan <fermin@tid.es> 0.7.1-1 (FIWARE-3.1.2-1)
- FIX avoid sending empty contextValue in notifyContext (breaks federation between context brokers instances)
- FIX 'Content-Type' taking into account charset 
- FIX 'Accept' taking into account list and charset

* Thu Aug 29 2013 Fermin Galan <fermin@tid.es> 0.7.0-1 (FIWARE-3.1.2-1)
- notifyContextRequest and notifyContextAvailabilityRequest support
- Proper processing of 'Content-Type' and 'Accept' headers in requests
- FIX wrong XML format in unsubscribeContextRequest operation
- FIX not-blocking notification messages when <reference> is not responding
- FIX cross-operation payload contamination
- FIX large request proper detection and response
- Improved registration and subscription ID validation

* Tue Jul 30 2013 Fermin Galan <fermin@tid.es> 0.6.0-1 (FIWARE-3.1.1-1)
- Support queryContext and discoverContextAvailability requests involving pattern entities without type
- Genaral improvement of NGSI functionality in requests involving entities or attributes without type    
- Default duration implementation for registerContext, subscribeContext and subscribeContextAvailability
- FIX adding proper Content-Type header in HTTP responses
- FIX proper semaphore releasing in some requests
- FIX not recover ONTIMEINTERVAL threads when -ngsi9 is used
- FIX large input buffers correctly taken care of

* Fri Jun 28 2013 Fermin Galan <fermin@tid.es> 0.5.0-1 (FIWARE-2.3.3-1)
- Resiliancy and recovery to database connection problems (now they don't break the broker with segfault)
- General improvement and enrichment of test harness, making them more resilient and stable
- Improvements in subscription processing, taking into account expiration in csubs collection queries
- Renaming option -cm -> -ngsi9
- Decoupling -ngsi9 and -fwdPort/fwdHost, now they can be uses indepently
- FIX creating ONTIMEINTERVAL threads at startup
- FIX changing name of databases for testharness (orion -> testharness) to avoid accidental deleting production database
- FIX add nc, curl and libxml2 to test RPM dependencies
- FIX now expiration is honoured in discoverContextAttribute
- FIX using 0 for -fwdPort to avoid registerContext loop with default command line
- Add verbose mode in accumulator-server.py
- Add number REST operation in accumulator-server.py
- Add garbage-collection.py script
- Other minor bugfixing

* Thu Jun 13 2013 Fermin Galan <fermin@tid.es> 0.4.1-1 (FIWARE-2.3.3-1)
- Bugfix in version reported by -version and curl ../version

* Thu Jun 13 2013 Fermin Galan <fermin@tid.es> 0.4.0-1 (FIWARE-2.3.3-1)
- REST interface for changing log and trace levels
- Memory leak fixes

* Mon Jun 04 2013 Fermín Galán <fermin@tid.es> 0.3.0-1 (FIWARE-2.3.3-1)
- CLI argument -logAppend
- Handlers for SIGUSR1 and SIGUSR2 signals to stop/resume logging
- Handlers for SIGTERM and SIGINT signals for smart exiting
- Fixing concurrency problems at mongo backend
- Memory leak fixes

* Mon May 27 2013 Fermín Galán <fermin@tid.es> 0.2.0-1 (FIWARE-2.3.2-1)
- All convenience functions implemented
- Associations extension support 
- Memory leak fixes
- Fix throttling processing in ONCHANGE subscriptions
- Fix expiration checking for ONCHANGE subscriptions
- Signal handler for SIGINT and SIGTERM. pidfile removed on SIGINT and SIGTERM
- CLI argument -localip
- MongoDB authentication implemented
- CLI argument -cm

* Tue May 14 2013 Fermín Galán <fermin@tid.es> 0.1.0-1 (FIWARE-2.3.2-1)
- Initial version of Orion Context Broker, based on old SAMSON Broker