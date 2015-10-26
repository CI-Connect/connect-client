#
# This spec file is now all you need.
#   $ rpmbuild -ba package/connect-client.spec
# The current checked-out revision will be built.
#

# change this 
%global tag %(git describe --exact-match 2>/dev/null || (git describe | cut -d- -f1,2 | tr - .))
%global date %(date +%Y%m%d)

Name:		connect-client
Version:	%{tag}
Release:	1%{?dist}
Summary:	connect client 
Group:		Gridware
License:	MIT
URL:		https://github.com/CI-Connect/connect-client
#Source0:	%{name}-%{tag}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch
Requires:	python-paramiko, perl >= 5.10

%description
Connect client

%prep
#%setup -q -n %{name}

%build

%install
# this is all very weird and probably very wrong
rm -rf %{buildroot}
(
	cd "$OLDPWD"
	# Allow only python 2.6 here
	env PYVERSIONS=26 ./install.sh %{buildroot}/usr

	#cp -p connect/bin/connect %{buildroot}%{_bindir}/
	#cp -p connect/bin/distribution %{buildroot}%{_bindir}/
	#cp -ap connect/lib/connect/ %{buildroot}%{_libdir}/connect
	#cp -p connect/etc/config.ini %{buildroot}%{_sysconfdir}/connect/
	# may not have all of the deps
	#cp -p scripts/tutorial/tutorial %{buildroot}%{_bindir}/tutorial
	# why are a crapload of pyc and pyo files getting created? who knows, lets
	# just delete them. this couldnt possibly bite us later
	## update - this doesnt work. the pyc files only seem to be present during
	## install stage. w t f
	#rm -f %{buildroot}%{_libdir}/connect/extensions/*.pyc
)
cd %{buildroot}
rm -f usr/pip.log usr/.gitignore
mv usr/etc etc
find .

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{_bindir}/connect
%{_bindir}/tutorial
%{_bindir}/distribution
/usr/lib/connect/*
%config(noreplace) %{_sysconfdir}/connect/config.ini

# insanity
%changelog
%(git log --date=raw --no-merges --format="* %%cd %%an <%%ae>%%%%- %%s%%%%" | tr %% '\012' | awk '/^*/ {"date -d@"$2" '"'+%%a %%b %%d %%Y'"'" | getline d; $2 = d; $3 = "";} {print;}')
