%bcond_without gnutls

# Macros needed by SELinux
%global selinuxtype targeted
%global moduletype  contrib
%global modulename  swtpm

Summary: TPM Emulator
Name:           swtpm
Version:        0.8.0
Release:        1%{?dist}
License:        BSD
Url:            https://github.com/stefanberger/swtpm
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Patch0001:      0001-swtpm_setup-fix-Werror-maybe-uninitialized.patch

BuildRequires:  make
BuildRequires:  git-core
BuildRequires:  automake
BuildRequires:  autoconf
BuildRequires:  libtool
BuildRequires:  libtpms-devel >= 0.6.0
BuildRequires:  glib2-devel
BuildRequires:  json-glib-devel
BuildRequires:  expect
BuildRequires:  net-tools
BuildRequires:  openssl-devel
BuildRequires:  socat
BuildRequires:  softhsm
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
BuildRequires:  tpm2-pkcs11 tpm2-pkcs11-tools tpm2-tools tpm2-abrmd

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

%package       tools-pkcs11
Summary:       Tools for creating a local CA based on a pkcs11 device
License:       BSD
Requires:      swtpm-tools = %{version}-%{release}
Requires:      tpm2-pkcs11 tpm2-pkcs11-tools tpm2-tools tpm2-abrmd
Requires:      expect gnutls-utils

%description   tools-pkcs11
Tools for creating a local CA based on a pkcs11 device

%prep
%autosetup -S git -p1

%build

NOCONFIGURE=1 ./autogen.sh
%configure \
%if %{with gnutls}
        --with-gnutls \
%endif
        --without-cuse

%make_build

%check
make %{?_smp_mflags} check VERBOSE=1

%install

%make_install
rm -f $RPM_BUILD_ROOT%{_libdir}/%{name}/*.{a,la,so}
rm $RPM_BUILD_ROOT%{_mandir}/man8/swtpm_cuse.8*

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
%{_mandir}/man5/swtpm-localca.conf.5*
%{_mandir}/man5/swtpm-localca.options.5*
%{_mandir}/man8/swtpm-localca.8*
%{_mandir}/man8/swtpm_localca.8*
%{_mandir}/man8/swtpm_setup.8*
%{_mandir}/man5/swtpm_setup.conf.5*
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
* Tue Nov 22 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.8.0-1
- Update to v0.8.0 release
  Resolves: rhbz#2092944

* Fri Jun 17 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-3.20211109gitb79fd91
- Disable OpenSSL FIPS mode to avoid libtpms failures
  Resolves: rhbz#2090219

* Mon Feb 21 2022 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-2.20211109gitb79fd91
- Add fix for CVE-2022-23645.
  Resolves: rhbz#2056518

* Fri Nov 12 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.7.0-1.20211109gitb79fd91
- Update to v0.7.0 release
  Resolves: rhbz#2021580 & rhbz#1990153

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com> - 0.6.0-3.20210607gitea627b3
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Mon Jul 12 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.6.0-2.20210607gitea627b3
- rebuilt with AM_* flags patch 

* Wed Jun 16 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.6.0-1.20210607gitea627b3
- new version
- Fixes: rhbz#1972785

* Wed Jun 16 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.5.2-7.20201226gite59c0c1
- Removed trouser dependency (used for vTPM 1.2, unsupported)
- Fixes: rhbz#1967919

* Wed Jun 16 2021 Mohan Boddu <mboddu@redhat.com> - 0.5.2-6.20201226gite59c0c1
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Tue May 18 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.5.2-5.20201226gite59c0c1
- Add -Wno-error=deprecated-declarations to fix build with OpenSSL 3.0.
- Fixes: rhbz#1958033

* Tue Apr 20 2021 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.5.2-4.20201226gite59c0c1
- Remove unnecessary twisted dependency.
- Fixes: rhbz#1935825

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 0.5.2-3.20201226gite59c0c1
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.2-2.20201226gite59c0c1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sat Dec 26 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.5.2-1.20201226gite59c0c1a
- Bugfixes for stable release

* Mon Dec 07 2020 Jeff Law <law@redhat.com> - 0.5.1-3.20201117git96f5a04c
- Avoid diagnostic from gcc-11

* Fri Nov 13 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.5.1-2.20201117git96f5a04c
- Another build of v0.5.1 after more fixes

* Fri Nov 13 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.5.1-1.20201007git390f5bd4
- Update to v0.5.1 addressing potential symlink attack issue (CVE-2020-28407)

* Wed Oct 7 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.5.0-1.20201007gitb931e109
- Update to v0.5.0 release

* Fri Aug 28 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.4.0-1.20200828git0c238a2
- Update to v0.4.0 release

* Thu Aug 27 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.3.4-2.20200711git80f0418
- Disable pkcs11 related test case running into GnuTLS locking bug

* Tue Aug 11 2020 Stefan Berger <stefanb@linux.ibm.com> - 0.3.4-1.20200711git80f0418
- Update to v0.3.4 release

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.3.0-3.20200218git74ae43b
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.3.0-2.20200218git74ae43b
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Mon Feb 24 2020 Marc-André Lureau <marcandre.lureau@redhat.com> - 0.3.0-1.20200218git74ae43b
- Update to v0.3.0 release

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.0-7.20191115git8dae4b3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Nov 15 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-6.20191018git8dae4b3
- follow stable-0.2.0 branch with fix of GnuTLS API call to get subject key ID

* Fri Oct 18 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-5.20191018git9227cf4
- follow stable-0.2.0 branch with swtpm_cert OID bugfix for TPM 2

* Tue Aug 13 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-4.20190801git13536aa
- run 'restorecon' on swtpm in post to get SELinux label on first install

* Thu Aug 01 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-3.20190801git13536aa
- follow stable-0.2.0 branch with some bug fixes

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.0-2.20190723gitf0b4137
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue Jul 23 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-1.20190723gitf0b4137
- follow stable-0.2.0 branch with some bug fixes

* Tue Jul 16 2019 Stefan Berger <stefanb@linux.ibm.com> - 0.2.0-0.20190716git374b669
- (tentative) v0.2.0 release of swtpm

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
