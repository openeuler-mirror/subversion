%define jdk_path /usr/lib/jvm/java

%define perl_vendorarch %(eval "`%{__perl} -V:installvendorarch`"; echo $installvendorarch)

%global svn_python_sitearch %{python3_sitearch}
%global svn_python %{__python3}

%bcond_with java

Summary: Subversion, a version control system.
Name: subversion
Version: 1.14.1
Release: 1
License: ASL 2.0
URL: https://subversion.apache.org/

Source0: https://www.apache.org/dist/subversion/subversion-%{version}.tar.bz2

Patch0: subversion-1.12.0-linking.patch
Patch1: subversion-1.14.0-testwarn.patch
Patch2: subversion-1.14.0-soversion.patch
Patch3: subversion-1.8.0-rubybind.patch
Patch4: subversion-1.8.5-swigplWall.patch

BuildRequires: autoconf libtool texinfo which swig gettext apr-devel apr-util-devel libserf-devel cyrus-sasl-devel sqlite-devel file-devel utf8proc-devel lz4-devel apr-util-openssl dbus-devel, libsecret-devel httpd-devel git chrpath
Requires: httpd

Provides: svn
Provides: %{name}-libs
Provides: %{name}-gnome
Provides: mod_dav_svn
Provides: %{name}-tools

Obsoletes: svn
Obsoletes: %{name}-libs
Obsoletes: %{name}-gnome
Obsoletes: mod_dav_svn
Obsoletes: %{name}-tools

%define swigdirs swig_pydir=%{svn_python_sitearch}/libsvn swig_pydir_extra=%{svn_python_sitearch}/svn

%description
Subversion exists to be universally recognized and adopted as an open-source, centralized version control system characterized by its reliability as a safe haven for valuable data; the simplicity of its model and usage; and its ability to support the needs of a wide variety of users and projects, from individuals to large-scale enterprise operations.

%package devel
Summary:  Development package for subversion
Requires: subversion%{?_isa} = %{version}-%{release}
Requires: apr-devel%{?_isa}, apr-util-devel%{?_isa}

%description devel
Development package for subversion.
%package_help
Requires: subversion = %{version}-%{release}

%package -n python3-%{name}
%{?python_provide:%python_provide python3-subversion}
Provides: %{name}-python = %{version}-%{release}
Provides: python3-%{name} = %{version}-%{release}
Provides: %{name}-python%{?_isa} = %{version}-%{release}
BuildRequires: python3-devel py3c-devel
Summary:  python3 bindings to the subversion libraries

%description -n python3-%{name}
python3 bindings to the subversion libraries

%package -n perl-%{name}
Summary:  perl bindings to the subversion libraries
Provides: %{name}-perl = %{version}-%{release}
Obsoletes: %{name}-perl
BuildRequires: perl-devel >= 2:5.8.0, perl-generators, perl(ExtUtils::MakeMaker) perl(Test::More), perl(ExtUtils::Embed)
Requires: %(eval `perl -V:version`; echo "perl(:MODULE_COMPAT_$version)")
Requires: subversion%{?_isa} = %{version}-%{release}

%description -n perl-%{name}
perl bindings to the subversion libraries

%if %{with java}
%package -n java-%{name}
Summary:  java bindings to the subversion libraries
Provides: %{name}-java = %{version}-%{release}
Obsoletes: %{name}-java
Provides: %{name}-javahl = %{version}-%{release}
Obsoletes: %{name}-javahl
Requires: subversion = %{version}-%{release}
BuildRequires: java-devel-openjdk zip, unzip junit
BuildArch: noarch

%description -n java-%{name}
java bindings to the subversion libraries
%endif

%package -n ruby-%{name}
Summary: Ruby bindings to the Subversion libraries
Provides: %{name}-ruby = %{version}-%{release}
Obsoletes: %{name}-ruby
BuildRequires: ruby-devel ruby rubygem(test-unit)
Requires: subversion%{?_isa} = %{version}-%{release}

%description -n ruby-%{name}
This package includes the Ruby bindings to the Subversion libraries.

%prep
%autosetup -n %{name}-%{version} -S git

%build
mv build-outputs.mk build-outputs.mk.old
export PYTHON=%{svn_python}
touch build/generator/swig/*.py
PATH=/usr/bin:$PATH ./autogen.sh --release

perl -pi -e 's|/usr/bin/env perl -w|/usr/bin/perl -w|' tools/hook-scripts/*.pl.in
perl -pi -e 's|/usr/bin/env python.*|%{svn_python}|' subversion/tests/cmdline/svneditor.py

export svn_cv_ruby_link="%{__cc} -shared"
export svn_cv_ruby_sitedir_libsuffix=""
export svn_cv_ruby_sitedir_archsuffix=""

export APACHE_LDFLAGS="-Wl,-z,relro,-z,now"
export CC=gcc CXX=g++ JAVA_HOME=%{jdk_path}

%configure --with-apr=%{_prefix} --with-apr-util=%{_prefix} \
        --disable-debug \
        --with-swig --with-serf=%{_prefix} \
        --with-ruby-sitedir=%{ruby_vendorarchdir} \
        --with-ruby-test-verbose=verbose \
        --with-apxs=%{_httpd_apxs} --disable-mod-activation \
        --with-apache-libexecdir=%{_httpd_moddir} \
        --disable-static --with-sasl=%{_prefix} \
        --with-libmagic=%{_prefix} \
        --with-gnome-keyring \
%if %{with java}
        --enable-javahl \
        --with-junit=%{_prefix}/share/java/junit.jar \
%endif
        --without-berkeley-db \
        || (cat config.log; exit 1)
make %{?_smp_mflags} all tools
make swig-py swig-py-lib %{swigdirs}
make swig-pl swig-pl-lib swig-rb swig-rb-lib
%if %{with java}
make javahl
%endif

%install
make install DESTDIR=$RPM_BUILD_ROOT
make install-swig-py %{swigdirs} DESTDIR=$RPM_BUILD_ROOT
make install-swig-pl-lib install-swig-rb DESTDIR=$RPM_BUILD_ROOT
make pure_vendor_install -C subversion/bindings/swig/perl/native \
        PERL_INSTALL_ROOT=$RPM_BUILD_ROOT
%if %{with java}
make install-javahl-java install-javahl-lib javahl_javadir=%{_javadir}
%endif
DESTDIR=$RPM_BUILD_ROOT

install -m 755 -d ${RPM_BUILD_ROOT}%{_sysconfdir}/subversion

mkdir -p ${RPM_BUILD_ROOT}{%{_httpd_modconfdir},%{_httpd_confdir}}

rm -rf ${RPM_BUILD_ROOT}%{_includedir}/subversion-*/*.txt \
       ${RPM_BUILD_ROOT}%{svn_python_sitearch}/*/*.{a,la}

rm -f ${RPM_BUILD_ROOT}%{_libdir}/libsvn_auth_*.so

find $RPM_BUILD_ROOT -type f \
    -a \( -name .packlist -o \( -name '*.bs' -a -empty \) \) \
    -print0 | xargs -0 rm -f

find $RPM_BUILD_ROOT%{_libdir}/perl5 -type f -perm 555 -print0 |
        xargs -0 chmod 755

rm -f ${RPM_BUILD_ROOT}%{_libdir}/libsvn_swig_*.{so,la,a}

rm -f ${RPM_BUILD_ROOT}%{ruby_vendorarchdir}/svn/ext/*.*a

rm -rvf tools/*/*.in tools/hook-scripts/mailer/tests

ln -f subversion/mod_authz_svn/INSTALL mod_authz_svn-INSTALL

sed -i "/^dependency_libs/{
     s, -l[^ ']*, ,g;
     s, -L[^ ']*, ,g;
     s,%{_libdir}/lib[^a][^p][^r][^ ']*.la, ,g;
     }"  $RPM_BUILD_ROOT%{_libdir}/*.la

install -Dpm 644 tools/client-side/bash_completion \
        $RPM_BUILD_ROOT%{_datadir}/bash-completion/completions/svn
for comp in svnadmin svndumpfilter svnlook svnsync svnversion; do
    ln -s svn \
        $RPM_BUILD_ROOT%{_datadir}/bash-completion/completions/${comp}
done

make install-tools DESTDIR=$RPM_BUILD_ROOT toolsdir=%{_bindir}
rm -f $RPM_BUILD_ROOT%{_bindir}/diff* $RPM_BUILD_ROOT%{_bindir}/x509-parser

sed -i "/^Requires.private/s, serf-1, ," \
    $RPM_BUILD_ROOT%{_datadir}/pkgconfig/libsvn_ra_serf.pc

rm $RPM_BUILD_ROOT%{_bindir}/svnauthz-validate
ln -s svnauthz $RPM_BUILD_ROOT%{_bindir}/svnauthz-validate

for f in svn-populate-node-origins-index fsfs-access-map \
    svnauthz svnauthz-validate svnmucc svnraisetreeconflict svnbench \
    svn-mergeinfo-normalizer fsfs-stats svnmover svnconflict; do
    echo %{_bindir}/$f
    if test -f $RPM_BUILD_ROOT%{_mandir}/man?/${f}.*; then
       echo %{_mandir}/man?/${f}.*
    fi
done | tee tools.files | sed 's/^/%%exclude /' > exclude.tools.files

%find_lang %{name}

cat %{name}.lang exclude.tools.files >> %{name}.files

#remove rpath
chrpath -d $RPM_BUILD_ROOT%{_bindir}/{svn,svnadmin,svndumpfilter,svnfsfs,svnlook,svnrdump,svnserve,svnsync,svnversion}

mkdir -p $RPM_BUILD_ROOT/etc/ld.so.conf.d
echo "%{_libdir}" > $RPM_BUILD_ROOT/etc/ld.so.conf.d/%{name}-%{_arch}.conf

%check
export LANG=C LC_ALL=C
export LD_LIBRARY_PATH=$RPM_BUILD_ROOT%{_libdir}
export MALLOC_PERTURB_=171 MALLOC_CHECK_=3
export LIBC_FATAL_STDERR_=1
export PYTHON=%{svn_python}
if ! make check CLEANUP=yes; then
   : Test suite failure.
   cat fails.log
   exit 1
fi
if ! make check-swig-pl check-swig-rb; then
   : Swig test failure.
   exit 1
fi
if ! make check-swig-py; then
   : Python swig test failure.
   exit 1
fi
# check-swig-rb omitted: it runs svnserve
%if %{with java}
make check-javahl
%endif

%preun

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%post devel -p /sbin/ldconfig

%postun devel -p /sbin/ldconfig

%post -n python3-%{name} -p /sbin/ldconfig

%postun -n python3-%{name} -p /sbin/ldconfig

%post -n perl-%{name} -p /sbin/ldconfig

%postun -n perl-%{name} -p /sbin/ldconfig

%post -n ruby-%{name} -p /sbin/ldconfig

%postun -n ruby-%{name} -p /sbin/ldconfig

%if %{with java}
%post -n java-%{name} -p /sbin/ldconfig

%postun -n java-%{name} -p /sbin/ldconfig
%endif

%files -f %{name}.files
%{!?_licensedir:%global license %%doc}
%license LICENSE NOTICE
%doc BUGS COMMITTERS INSTALL README CHANGES
%doc mod_authz_svn-INSTALL
%{_bindir}/*
%{_datadir}/bash-completion/
%dir %{_sysconfdir}/subversion
%{!?_licensedir:%global license %%doc}
%license LICENSE NOTICE
%{_libdir}/libsvn*.so.*
%exclude %{_libdir}/libsvn_swig_perl*
%exclude %{_libdir}/libsvn_swig_ruby*
%if %{with java}
%{_libdir}/libsvnjavahl-*.so
%endif
%doc tools/hook-scripts tools/backup tools/bdb tools/examples tools/xslt
%{_libdir}/httpd/modules/mod_*.so
%config(noreplace) /etc/ld.so.conf.d/*

%files -n python3-subversion
%{python3_sitearch}/svn
%{python3_sitearch}/libsvn

%files devel
%{_includedir}/subversion-1
%{_libdir}/libsvn*.*a
%{_libdir}/libsvn*.so
%{_datadir}/pkgconfig/*.pc
%exclude %{_libdir}/libsvn_swig_perl*
%if %{with java}
%exclude %{_libdir}/libsvnjavahl-*.so
%endif

%files help
%{_mandir}/man*/*
%exclude %{_mandir}/man*/*::*

%files -n perl-%{name}
%{perl_vendorarch}/auto/SVN
%{perl_vendorarch}/SVN
%{_libdir}/libsvn_swig_perl*
%{_mandir}/man*/*::*

%files -n ruby-%{name}
%{_libdir}/libsvn_swig_ruby*
%{ruby_vendorarchdir}/svn

%if %{with java}
%files -n java-%{name}
%{_javadir}/svn-javahl.jar
%endif

%changelog
* Tue Nov 30 2021 fuanan<fuanan3@huawei.com> - 1.14.1-1
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:update version to 1.14.1

* Mon Sep 6 2021 panxiaohe<panxiaohe@huawei.com> - 1.14.0-4
- remove rpath and runpath of exec files and libraries

* Sat Jun 19 2021 panxiaohe<panxiaohe@huawei.com> - 1.14.0-3
- dismiss the dependence of libdb

* Mon Feb 22 2021 yixiangzhike<zhangxingliang3@huawei.com> - 1.14.0-2
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:Fix CVE-2020-17525

* Sat Aug 1 2020 yang_zhuang_zhuang<yangzhuangzhuang1@huawei.com> - 1.14.0-1
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:update version to 1.14.0

* Wed Oct 30 2019 chengquan<chengquan3@huawei.com> - 1.10.6-2
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:remove junit require with java package

* Tue Aug 27 2019 openEuler Buildteam <buildteam@openeuler.org> - 1.10.6-1
- Package init

