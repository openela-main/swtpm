%bcond_without gnutls

%global gitdate     20211109
%global gitcommit   b79fd91c4b4a74c9c5027b517c5036952c5525db
%global gitshortcommit  %(c=%{gitcommit}; echo ${c:0:7})

# Macros needed by SELinux
%global selinuxtype targeted
%global moduletype  contrib
%global modulename  swtpm

Summary: TPM Emulator
Name:           swtpm
Version:        0.7.0
Release:        4.%{gitdate}git%{gitshortcommit}%{?dist}
License:        BSD
Url:            http://github.com/stefanberger/swtpm
Source0:        %{url}/archive/%{gitcommit}/%{name}-%{gitshortcommit}.tar.gz
ExcludeArch:    i686
Patch0001:      0001-swtpm-Check-header-size-indicator-against-expected-s.patch
Patch0002:      0001-swtpm-Disable-OpenSSL-FIPS-mode-to-avoid-libtpms-fai.patch
Patch0003:      0001-swtpm_localca-Test-for-available-issuercert-before-c.patch

BuildRequires: make
BuildRequires:  git-core
BuildRequires:  automake
BuildRequires:  autoconf
BuildRequires:  libtool
BuildRequires:  libtpms-devel >= 0.6.0
BuildRequires:  expect
BuildRequires:  net-tools
BuildRequires:  openssl-devel
BuildRequires:  socat
BuildRequires:  softhsm
BuildRequires:  json-glib-devel
%if %{with gnutls}
BuildRequires:  gnutls >= 3.4.0
BuildRequires:  gnutls-devel
BuildRequires:  gnutls-utils
BuildRequires:  libtasn1-devel
BuildRequires:  libtasn1
%endif
BuildRequires:  selinux-policy-devel
BuildRequires:  gcc
BuildRequires:  libseccomp-devel
BuildRequires:  tpm2-tools tpm2-abrmd
BuildRequires:  python3-devel

Requires:       %{name}-libs = %{version}-%{release}
Requires:       libtpms >= 0.6.0
%{?selinux_requires}

%description
TPM emulator built on libtpms providing TPM functionality for QEMU VMs

%package        libs
Summary:        Private libraries for swtpm TPM emulators
License:        BSD

%description    libs
A private library with callback functions for libtpms based swtpm TPM emulator

%package        devel
Summary:        Include files for the TPM emulator's CUSE interface for usage by clients
License:        BSD
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description    devel
Include files for the TPM emulator's CUSE interface.

%package        tools
Summary:        Tools for the TPM emulator
License:        BSD
Requires:       swtpm = %{version}-%{release}
Requires:       bash gnutls-utils

%description    tools
Tools for the TPM emulator from the swtpm package

%package        tools-pkcs11
Summary:        Tools for creating a local CA based on a TPM pkcs11 device
License:        BSD
Requires:       swtpm-tools = %{version}-%{release}
Requires:       tpm2-tools tpm2-abrmd
Requires:       expect gnutls-utils

%description   tools-pkcs11
Tools for creating a local CA based on a pkcs11 device

%prep
%autosetup -S git -n %{name}-%{gitcommit} -p1

%build

NOCONFIGURE=1 ./autogen.sh
%configure \
%if %{with gnutls}
        --with-gnutls \
%endif
        --without-cuse \
        --without-tpm1

%make_build V=1

%check
make %{?_smp_mflags} check VERBOSE=1

%install

%make_install
rm -f $RPM_BUILD_ROOT%{_libdir}/%{name}/*.{a,la,so}

%post
for pp in /usr/share/selinux/packages/swtpm.pp \
          /usr/share/selinux/packages/swtpm_svirt.pp; do
  %selinux_modules_install -s %{selinuxtype} ${pp}
done
restorecon %{_bindir}/swtpm

%postun
if [ $1 -eq  0 ]; then
  for p in swtpm swtpm_svirt; do
    %selinux_modules_uninstall -s %{selinuxtype} $p
  done
fi

%posttrans
%selinux_relabel_post -s %{selinuxtype}

%ldconfig_post libs
%ldconfig_postun libs

%files
%license LICENSE
%doc README
%{_bindir}/swtpm
%{_mandir}/man8/swtpm.8*
%{_datadir}/selinux/packages/swtpm.pp
%{_datadir}/selinux/packages/swtpm_svirt.pp

%files libs
%license LICENSE
%doc README

%dir %{_libdir}/%{name}
%{_libdir}/%{name}/libswtpm_libtpms.so.0
%{_libdir}/%{name}/libswtpm_libtpms.so.0.0.0

%files devel
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.h
%{_mandir}/man3/swtpm_ioctls.3*

%files tools
%doc README
%{_bindir}/swtpm_bios
%if %{with gnutls}
%{_bindir}/swtpm_cert
%endif
%{_bindir}/swtpm_setup
%{_bindir}/swtpm_ioctl
%{_bindir}/swtpm_localca
%{_mandir}/man8/swtpm_bios.8*
%{_mandir}/man8/swtpm_cert.8*
%{_mandir}/man8/swtpm_ioctl.8*
%{_mandir}/man8/swtpm-localca.conf.8*
%{_mandir}/man8/swtpm-localca.options.8*
%{_mandir}/man8/swtpm-localca.8*
%{_mandir}/man8/swtpm_localca.8*
%{_mandir}/man8/swtpm_setup.8*
%{_mandir}/man8/swtpm_setup.conf.8*
%config(noreplace) %{_sysconfdir}/swtpm_setup.conf
%config(noreplace) %{_sysconfdir}/swtpm-localca.options
%config(noreplace) %{_sysconfdir}/swtpm-localca.conf
%dir %{_datadir}/swtpm
%{_datadir}/swtpm/swtpm-localca
%{_datadir}/swtpm/swtpm-create-user-config-files
%attr( 750, tss, root) %{_localstatedir}/lib/swtpm-localca

%files tools-pkcs11
%{_mandir}/man8/swtpm-create-tpmca.8*
%{_datadir}/swtpm/swtpm-create-tpmca

%changelog
* Mon Jul 18 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-4.20211109gitb79fd91
- swtpm_localca: Test for available issuercert before creating CA
  Resolves: rhbz#2100508

* Mon Jun 20 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-3.20211109gitb79fd91
- Disable OpenSSL FIPS mode to avoid libtpms failures
  Resolves: rhbz#2097947

* Mon Feb 21 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-2.20211109gitb79fd91
- Add fix for CVE-2022-23645.
  Resolves: rhbz#2056517

* Tue Jan 04 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-1.20211109gitb79fd91
- Rebase to 0.7.0, disable TPM 1.2.
  Resovles: rhbz#2029612

* Thu Sep 16 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.6.0-2.20210607gitea627b3
- rebuilt with missing CFLAGS fix.

* Mon Jun 28 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.6.0-1.20210607gitea627b3
- Update to 0.6.0.
  Resolves: rhbz#1972783

* Tue Dec  1 20:40:07 +04 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.4.2-1.20201201git2df14e3
- Update to 0.4.2, to address potential symlink vulnerabilities (CVE-2020-28407).
  Resolves: rhbz#1906043

* Thu Sep 24 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.4.0-3.20200828git0c238a2
- swtpm_setup: Add missing .config path when using ${HOME}. Resolves: rhbz#1881418

* Thu Sep 17 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.4.0-2.20200828git0c238a2
- Backport fixes from 0.4.0 stable branch. Resolves: rhbz#1868375
  (fixes usage of swtpm-localca with passwords when signing keys)

* Sat Sep 12 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.4.0-1.20200828git0c238a2
- Update to v0.4.0. Resolves: rhbz#1868375

* Thu May 28 2020 Marc-André Lureau <marcandre.lureau@gmail.com> - 0.3.0-1.20200218git74ae43b
- Update to v0.3.0. Fixes rhbz#1809778
- exclude i686 build

* Mon Jan 27 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.2.0-2.20200127gitff5a83b
- Update to latest 0.2-stable branch, fix random test failure. rhbz#1782451

* Fri Oct 18 2019 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.2.0-1.20191018git9227cf4
- rebuilt

* Tue Aug 13 2019 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.1.0-1.20190425gitca85606.1
- Fix SELinux labels on /usr/bin/swtpm installation rhbz#1739994

* Thu Apr 25 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.1.0-0.20190425gitca85606
- pick up bug fixes

* Mon Feb 04 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.1.0-0.20190204git2c25d13.1
- v0.1.0 release of swtpm

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.0-0.20181212git8b9484a.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Dec 12 2018 Stefan Berger <stefanb@linux.ibm.com> - 0.1.0-0.20181212git8b9484a
- Follow improvements in swtpm repo primarily related to fixes for 'ubsan'

* Tue Nov 06 2018 Stefan Berger <stefanb@linux.ibm.com> - 0.1.0-0.20181106git05d8160
- Follow improvements in swtpm repo
- Remove ownership change of swtpm_setup.sh; have root own the file as required

* Wed Oct 31 2018 Stefan Berger <stefanb@linux.ibm.com> - 0.1.0-0.20181031gitc782a85
- Follow improvements and fixes in swtpm

* Tue Oct 02 2018 Stefan Berger <stefanb@linux.vnet.ibm.com> - 0.1.0-0.20181002git0143c41
- Fixes to SELinux policy
- Improvements on various other parts
* Tue Sep 25 2018 Stefan Berger <stefanb@linux.vnet.ibm.com> - 0.1.0-0.20180924gitce13edf
- Initial Fedora build
* Mon Sep 17 2018 Stefan Berger <stefanb@linux.vnet.ibm.com> - 0.1.0-0.20180918git67d7ea3
- Created initial version of rpm spec files
- Version is now 0.1.0
- Bugzilla for this spec: https://bugzilla.redhat.com/show_bug.cgi?id=1611829
