#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors:
#   Thomas Woerner <twoerner@redhat.com>
#
# Based on ipa-client-install code
#
# Copyright (C) 2017  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview'],
}

DOCUMENTATION = '''
---
module: ipaserver_test
short description:
description:
options:
author:
    - Thomas Woerner
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import os
import sys
import six
import inspect

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_ipa_server import (
    AnsibleModuleLog, options, adtrust_imported, kra_imported, PKIIniLoader,
    random, MIN_DOMAIN_LEVEL, MAX_DOMAIN_LEVEL, check_zone_overlap,
    redirect_stdout, validate_dm_password, validate_admin_password,
    NUM_VERSION, is_ipa_configured, sysrestore, paths, bindinstance,
    read_cache, ca, tasks, check_ldap_conf, timeconf, httpinstance,
    check_dirsrv, ScriptError, get_fqdn, verify_fqdn, BadHostError,
    validate_domain_name, load_pkcs12, IPA_PYTHON_VERSION
)

if six.PY3:
    unicode = str


def main():
    ansible_module = AnsibleModule(
        argument_spec = dict(
            ### basic ###
            force=dict(required=False, type='bool', default=False),
            dm_password=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            master_password=dict(required=False, no_log=True),
            domain=dict(required=False),
            realm=dict(required=False),
            hostname=dict(required=False),
            ca_cert_files=dict(required=False, type='list', default=[]),
            no_host_dns=dict(required=False, type='bool', default=False),
            pki_config_override=dict(required=False),
            ### server ###
            setup_adtrust=dict(required=False, type='bool', default=False),
            setup_kra=dict(required=False, type='bool', default=False),
            setup_dns=dict(required=False, type='bool', default=False),
            idstart=dict(required=False, type='int'),
            idmax=dict(required=False, type='int'),
            # no_hbac_allow
            no_pkinit=dict(required=False, type='bool', default=False),
            # no_ui_redirect
            dirsrv_config_file=dict(required=False),
            ### ssl certificate ###
            dirsrv_cert_files=dict(required=False, type='list', default=None),
            http_cert_files=dict(required=False, type='list', defaullt=None),
            pkinit_cert_files=dict(required=False, type='list', default=None),
            dirsrv_pin=dict(required=False),
            http_pin=dict(required=False),
            pkinit_pin=dict(required=False),
            dirsrv_cert_name=dict(required=False),
            http_cert_name=dict(required=False),
            pkinit_cert_name=dict(required=False),
            ### client ###
            # mkhomedir
            ntp_servers=dict(required=False, type='list', default=None),
            ntp_pool=dict(required=False, default=None),
            no_ntp=dict(required=False, type='bool', default=False),
            # ssh_trust_dns
            # no_ssh
            # no_sshd
            # no_dns_sshfp
            ### certificate system ###
            external_ca=dict(required=False, type='bool', default=False),
            external_ca_type=dict(required=False),
            external_ca_profile=dict(required=False),
            external_cert_files=dict(required=False, type='list', default=None),
            subject_base=dict(required=False),
            ca_subject=dict(required=False),
            # ca_signing_algorithm
            ### dns ###
            allow_zone_overlap=dict(required=False, type='bool', default=False),
            reverse_zones=dict(required=False, type='list', default=[]),
            no_reverse=dict(required=False, type='bool', default=False),
            auto_reverse=dict(required=False, type='bool', default=False),
            zonemgr=dict(required=False),
            forwarders=dict(required=False, type='list', default=[]),
            no_forwarders=dict(required=False, type='bool', default=False),
            auto_forwarders=dict(required=False, type='bool', default=False),
            forward_policy=dict(default=None, choices=['first', 'only']),
            no_dnssec_validation=dict(required=False, type='bool',
                                      default=False),
            ### ad trust ###
            enable_compat=dict(required=False, type='bool', default=False),
            netbios_name=dict(required=False),
            rid_base=dict(required=False, type='int', default=1000),
            secondary_rid_base=dict(required=False, type='int',
                                    default=100000000),

            ### additional ###
        ),
        supports_check_mode = True,
    )

    ansible_module._ansible_debug = True
    ansible_log = AnsibleModuleLog(ansible_module)

    # set values ############################################################

    ### basic ###
    options.force = ansible_module.params.get('force')
    options.dm_password = ansible_module.params.get('dm_password')
    options.admin_password = ansible_module.params.get('password')
    options.master_password = ansible_module.params.get('master_password')
    options.domain_name = ansible_module.params.get('domain')
    options.realm_name = ansible_module.params.get('realm')
    options.host_name = ansible_module.params.get('hostname')
    options.ca_cert_files = ansible_module.params.get('ca_cert_files')
    options.no_host_dns = ansible_module.params.get('no_host_dns')
    options.pki_config_override = ansible_module.params.get(
        'pki_config_override')
    ### server ###
    options.setup_adtrust = ansible_module.params.get('setup_adtrust')
    options.setup_dns = ansible_module.params.get('setup_dns')
    options.setup_kra = ansible_module.params.get('setup_kra')
    options.idstart = ansible_module.params.get('idstart')
    options.idmax = ansible_module.params.get('idmax')
    # no_hbac_allow
    options.no_pkinit = ansible_module.params.get('no_pkinit')
    # no_ui_redirect
    options.dirsrv_config_file = ansible_module.params.get('dirsrv_config_file')
    ### ssl certificate ###
    options.dirsrv_cert_files = ansible_module.params.get('dirsrv_cert_files')
    options.http_cert_files = ansible_module.params.get('http_cert_files')
    options.pkinit_cert_files = ansible_module.params.get('pkinit_cert_files')
    options.dirsrv_pin = ansible_module.params.get('dirsrv_pin')
    options.http_pin = ansible_module.params.get('http_pin')
    options.pkinit_pin = ansible_module.params.get('pkinit_pin')
    options.dirsrv_cert_name = ansible_module.params.get('dirsrv_cert_name')
    options.http_cert_name = ansible_module.params.get('http_cert_name')
    options.pkinit_cert_name = ansible_module.params.get('pkinit_cert_name')
    ### client ###
    # mkhomedir
    options.ntp_servers = ansible_module.params.get('ntp_servers')
    options.ntp_pool = ansible_module.params.get('ntp_pool')
    options.no_ntp = ansible_module.params.get('no_ntp')
    # ssh_trust_dns
    # no_ssh
    # no_sshd
    # no_dns_sshfp
    ### certificate system ###
    options.external_ca = ansible_module.params.get('external_ca')
    options.external_ca_type = ansible_module.params.get('external_ca_type')
    options.external_ca_profile = ansible_module.params.get(
        'external_ca_profile')
    options.external_cert_files = ansible_module.params.get(
        'external_cert_files')
    options.subject_base = ansible_module.params.get('subject_base')
    options.ca_subject = ansible_module.params.get('ca_subject')
    # ca_signing_algorithm
    ### dns ###
    options.allow_zone_overlap = ansible_module.params.get('allow_zone_overlap')
    options.reverse_zones = ansible_module.params.get('reverse_zones')
    options.no_reverse = ansible_module.params.get('no_reverse')
    options.auto_reverse = ansible_module.params.get('auto_reverse')
    options.zonemgr = ansible_module.params.get('zonemgr')
    options.forwarders = ansible_module.params.get('forwarders')
    options.no_forwarders = ansible_module.params.get('no_forwarders')
    options.auto_forwarders = ansible_module.params.get('auto_forwarders')
    options.forward_policy = ansible_module.params.get('forward_policy')
    options.no_dnssec_validation = ansible_module.params.get(
        'no_dnssec_validation')
    ### ad trust ###
    options.enable_compat = ansible_module.params.get('enable_compat')
    options.netbios_name = ansible_module.params.get('netbios_name')
    options.rid_base = ansible_module.params.get('rid_base')
    options.secondary_rid_base = ansible_module.params.get('secondary_rid_base')

    ### additional ###
    options.kasp_db_file = None

    # version specific ######################################################

    if options.setup_adtrust and not adtrust_imported:
        #if "adtrust" not in options._allow_missing:
        ansible_module.fail_json(msg="adtrust can not be imported")
        #else:
        #  options.setup_adtrust = False
        #  ansible_module.warn(msg="adtrust is not supported, disabling")

    if options.setup_kra and not kra_imported:
        #if "kra" not in options._allow_missing:
        ansible_module.fail_json(msg="kra can not be imported")
        #else:
        #  options.setup_kra = False
        #  ansible_module.warn(msg="kra is not supported, disabling")

    if options.pki_config_override is not None:
        if PKIIniLoader is None:
            ansible_module.warn("The use of pki_config_override is not "
                                "supported for this IPA version")
        else:
            # From DogtagInstallInterface @pki_config_override.validator
            try:
                PKIIniLoader.verify_pki_config_override(
                    options.pki_config_override)
            except ValueError as e:
                ansible_module.fail_json(
                    msg="pki_config_override: %s" % str(e))

    # default values ########################################################

    # idstart and idmax
    if options.idstart is None:
        options.idstart = random.randint(1, 10000) * 200000
    if options.idmax is None or options.idmax == 0:
        options.idmax = options.idstart + 199999

    #class ServerInstallInterface(ServerCertificateInstallInterface,
    #                             client.ClientInstallInterface,
    #                             ca.CAInstallInterface,
    #                             kra.KRAInstallInterface,
    #                             dns.DNSInstallInterface,
    #                             adtrust.ADTrustInstallInterface,
    #                             conncheck.ConnCheckInterface,
    #                             ServerUninstallInterface):

    # ServerInstallInterface.__init__ #######################################
    try:
        self = options

        # If any of the key file options are selected, all are required.
        cert_file_req = (self.dirsrv_cert_files, self.http_cert_files)
        cert_file_opt = (self.pkinit_cert_files,)
        if not self.no_pkinit:
            cert_file_req += cert_file_opt
        if self.no_pkinit and self.pkinit_cert_files:
            raise RuntimeError(
                "--no-pkinit and --pkinit-cert-file cannot be specified "
                "together"
            )
        if any(cert_file_req + cert_file_opt) and not all(cert_file_req):
            raise RuntimeError(
                "--dirsrv-cert-file, --http-cert-file, and --pkinit-cert-file "
                "or --no-pkinit are required if any key file options are used."
            )

        if not self.interactive:
            if self.dirsrv_cert_files and self.dirsrv_pin is None:
                raise RuntimeError(
                    "You must specify --dirsrv-pin with --dirsrv-cert-file")
            if self.http_cert_files and self.http_pin is None:
                raise RuntimeError(
                    "You must specify --http-pin with --http-cert-file")
            if self.pkinit_cert_files and self.pkinit_pin is None:
                raise RuntimeError(
                    "You must specify --pkinit-pin with --pkinit-cert-file")

        if not self.setup_dns:
            if self.forwarders:
                raise RuntimeError(
                    "You cannot specify a --forwarder option without the "
                    "--setup-dns option")
            if self.auto_forwarders:
                raise RuntimeError(
                    "You cannot specify a --auto-forwarders option without "
                    "the --setup-dns option")
            if self.no_forwarders:
                raise RuntimeError(
                    "You cannot specify a --no-forwarders option without the "
                    "--setup-dns option")
            if self.forward_policy:
                raise RuntimeError(
                    "You cannot specify a --forward-policy option without the "
                    "--setup-dns option")
            if self.reverse_zones:
                raise RuntimeError(
                    "You cannot specify a --reverse-zone option without the "
                    "--setup-dns option")
            if self.auto_reverse:
                raise RuntimeError(
                    "You cannot specify a --auto-reverse option without the "
                    "--setup-dns option")
            if self.no_reverse:
                raise RuntimeError(
                    "You cannot specify a --no-reverse option without the "
                    "--setup-dns option")
            if self.no_dnssec_validation:
                raise RuntimeError(
                    "You cannot specify a --no-dnssec-validation option "
                    "without the --setup-dns option")
        elif self.forwarders and self.no_forwarders:
            raise RuntimeError(
                "You cannot specify a --forwarder option together with "
                "--no-forwarders")
        elif self.auto_forwarders and self.no_forwarders:
            raise RuntimeError(
                "You cannot specify a --auto-forwarders option together with "
                "--no-forwarders")
        elif self.reverse_zones and self.no_reverse:
            raise RuntimeError(
                "You cannot specify a --reverse-zone option together with "
                "--no-reverse")
        elif self.auto_reverse and self.no_reverse:
            raise RuntimeError(
                "You cannot specify a --auto-reverse option together with "
                "--no-reverse")

        if not self.setup_adtrust:
            if self.add_agents:
                raise RuntimeError(
                    "You cannot specify an --add-agents option without the "
                    "--setup-adtrust option")

            if self.enable_compat:
                raise RuntimeError(
                    "You cannot specify an --enable-compat option without the "
                    "--setup-adtrust option")

            if self.netbios_name:
                raise RuntimeError(
                    "You cannot specify a --netbios-name option without the "
                    "--setup-adtrust option")

            if self.no_msdcs:
                raise RuntimeError(
                    "You cannot specify a --no-msdcs option without the "
                    "--setup-adtrust option")

        if not hasattr(self, 'replica_install'):
            if self.external_cert_files and self.dirsrv_cert_files:
                raise RuntimeError(
                    "Service certificate file options cannot be used with the "
                    "external CA options.")

            if self.external_ca_type and not self.external_ca:
                raise RuntimeError(
                    "You cannot specify --external-ca-type without "
                    "--external-ca")

            if self.external_ca_profile and not self.external_ca:
                raise RuntimeError(
                    "You cannot specify --external-ca-profile without "
                    "--external-ca")

            if self.uninstalling:
                if (self.realm_name or self.admin_password or
                        self.master_password):
                    raise RuntimeError(
                        "In uninstall mode, -a, -r and -P options are not "
                        "allowed")
            elif not self.interactive:
                if (not self.realm_name or not self.dm_password or
                        not self.admin_password):
                    raise RuntimeError(
                        "In unattended mode you need to provide at least -r, "
                        "-p and -a options")
                if self.setup_dns:
                    if (not self.forwarders and
                            not self.no_forwarders and
                            not self.auto_forwarders):
                        raise RuntimeError(
                            "You must specify at least one of --forwarder, "
                            "--auto-forwarders, or --no-forwarders options")

            any_ignore_option_true = any(
                [self.ignore_topology_disconnect, self.ignore_last_of_role])
            if any_ignore_option_true and not self.uninstalling:
                raise RuntimeError(
                    "'--ignore-topology-disconnect/--ignore-last-of-role' "
                    "options can be used only during uninstallation")

            if self.idmax < self.idstart:
                raise RuntimeError(
                    "idmax (%s) cannot be smaller than idstart (%s)" %
                    (self.idmax, self.idstart))
        else:
            # replica installers
            if self.servers and not self.domain_name:
                raise RuntimeError(
                    "The --server option cannot be used without providing "
                    "domain via the --domain option")

            if self.setup_dns:
                if (not self.forwarders and
                        not self.no_forwarders and
                        not self.auto_forwarders):
                    raise RuntimeError(
                        "You must specify at least one of --forwarder, "
                        "--auto-forwarders, or --no-forwarders options")

    except RuntimeError as e:
        ansible_module.fail_json(msg=e)








    # #######################################################################

    # If any of the key file options are selected, all are required.
    cert_file_req = (options.dirsrv_cert_files, options.http_cert_files)
    cert_file_opt = (options.pkinit_cert_files,)
    if not options.no_pkinit:
        cert_file_req += cert_file_opt
    if options.no_pkinit and options.pkinit_cert_files:
        ansible_module.fail_json(
            msg="no-pkinit and pkinit-cert-file cannot be specified together"
        )
    if any(cert_file_req + cert_file_opt) and not all(cert_file_req):
        ansible_module.fail_json(
            msg="dirsrv-cert-file, http-cert-file, and pkinit-cert-file "
            "or no-pkinit are required if any key file options are used."
        )

    if not options.interactive:
        if options.dirsrv_cert_files and options.dirsrv_pin is None:
            ansible_module.fail_json(
                msg="You must specify dirsrv-pin with dirsrv-cert-file")
        if options.http_cert_files and options.http_pin is None:
            ansible_module.fail_json(
                msg="You must specify http-pin with http-cert-file")
        if options.pkinit_cert_files and options.pkinit_pin is None:
            ansible_module.fail_json(
                msg="You must specify pkinit-pin with pkinit-cert-file")

    if not options.setup_dns:
        # lists
        for x in [ "forwarders", "reverse_zones" ]:
            if len(getattr(options, x)) > 1:
                ansible_module.fail_json(
                    msg="You cannot specify %s without setting setup-dns" % x)
        # bool and str values
        for x in [ "auto_forwarders", "no_forwarders",
                   "auto_reverse", "no_reverse", "no_dnssec_validation",
                   "forward_policy" ]:
            if getattr(options, x) == True:
                ansible_module.fail_json(
                    msg="You cannot specify %s without setting setup-dns" % x)

    elif len(options.forwarders) > 0 and options.no_forwarders:
        ansible_module.fail_json(
            msg="You cannot specify forwarders together with no-forwarders")
    elif options.auto_forwarders and options.no_forwarders:
        ansible_module.fail_json(
            msg="You cannot specify auto-forwarders together with no-forwarders")
    elif len(options.reverse_zones) > 0 and options.no_reverse:
        ansible_module.fail_json(
            msg="You cannot specify reverse-zones together with no-reverse")
    elif options.auto_reverse and options.no_reverse:
        ansible_module.fail_json(
            msg="You cannot specify auto-reverse together with no-reverse")

    if not hasattr(self, 'replica_install'):
        if options.external_cert_files and options.dirsrv_cert_files:
            ansible_module.fail_json(
                msg="Service certificate file options cannot be used with the "
                "external CA options.")

        if options.external_ca_type and not options.external_ca:
            ansible_module.fail_json(
                msg="You cannot specify external-ca-type without external-ca")

        #if options.uninstalling:
        #    if (options.realm_name or options.admin_password or
        #            options.master_password):
        #        ansible_module.fail_json(
        #            msg="In uninstall mode, -a, -r and -P options are not "
        #            "allowed")
        #elif not options.interactive:
        #    if (not options.realm_name or not options.dm_password or
        #            not options.admin_password):
        #        ansible_module.fail_json(msg=
        #            "In unattended mode you need to provide at least -r, "
        #            "-p and -a options")
        #    if options.setup_dns:
        #        if (not options.forwarders and
        #                not options.no_forwarders and
        #                not options.auto_forwarders):
        #            ansible_module.fail_json(msg=
        #                "You must specify at least one of --forwarder, "
        #                "--auto-forwarders, or --no-forwarders options")
        if (not options.realm_name or not options.dm_password or
                not options.admin_password):
            ansible_module.fail_json(
                msg="You need to provide at least realm_name, dm_password "
                "and admin_password")
        if options.setup_dns:
            if len(options.forwarders) < 1 and not options.no_forwarders and \
               not options.auto_forwarders:
                ansible_module.fail_json(
                    msg="You must specify at least one of forwarders, "
                    "auto-forwarders or no-forwarders")

        #any_ignore_option_true = any(
        #    [options.ignore_topology_disconnect, options.ignore_last_of_role])
        #if any_ignore_option_true and not options.uninstalling:
        #    ansible_module.fail_json(
        #        msg="ignore-topology-disconnect and ignore-last-of-role "
        #        "can be used only during uninstallation")

        if options.idmax < options.idstart:
            ansible_module.fail_json(
                msg="idmax (%s) cannot be smaller than idstart (%s)" %
                (options.idmax, options.idstart))

    # validation #############################################################

    if options.dm_password is None:
        ansible_module.fail_json(msg="Directory Manager password required")

    if options.admin_password is None:
        ansible_module.fail_json(msg="IPA admin password required")

    # validation ############################################################

    # domain_level
    if options.domain_level < MIN_DOMAIN_LEVEL:
        ansible_module.fail_json(
            msg="Domain Level cannot be lower than %d" % MIN_DOMAIN_LEVEL)
    elif options.domain_level > MAX_DOMAIN_LEVEL:
        ansible_module.fail_json(
            msg="Domain Level cannot be higher than %d" % MAX_DOMAIN_LEVEL)

    # dirsrv_config_file
    if options.dirsrv_config_file is not None:
        if not os.path.exists(options.dirsrv_config_file):
            ansible_module.fail_json(
                msg="File %s does not exist." % options.dirsrv_config_file)

    # domain_name
    if (options.setup_dns and not options.allow_zone_overlap and \
        options.domain_name is not None):
        try:
            check_zone_overlap(options.domain_name, False)
        except ValueError as e:
            ansible_module.fail_json(msg=str(e))

    # dm_password
    with redirect_stdout(ansible_log):
        validate_dm_password(options.dm_password)

    # admin_password
    with redirect_stdout(ansible_log):
        validate_admin_password(options.admin_password)

    # pkinit is not supported on DL0, don't allow related options

    """
    # replica install: if not options.replica_file is None:
    if (not options._replica_install and \
        not options.domain_level > DOMAIN_LEVEL_0) or \
        (options._replica_install and options.replica_file is not None):
        if (options.no_pkinit or options.pkinit_cert_files is not None or
                options.pkinit_pin is not None):
            ansible_module.fail_json(
                msg="pkinit on domain level 0 is not supported. Please "
                "don't use any pkinit-related options.")
        options.no_pkinit = True
    """



    if options.setup_dns:
        if len(options.forwarders) < 1 and not options.no_forwarders and \
           not options.auto_forwarders:
            ansible_module.fail_json(
                msg="You must specify at least one of forwarders, "
                "auto-forwarders or no-forwarders")

    if NUM_VERSION >= 40200 and options.master_password and \
       not options.external_cert_files:
        ansible_module.warn("Specifying kerberos master-password is deprecated")

    options._installation_cleanup = True
    if not options.external_ca and not options.external_cert_files and \
       is_ipa_configured():
        options._installation_cleanup = False
        ansible_module.log(
            "IPA server is already configured on this system. If you want "
            "to reinstall the IPA server, please uninstall it first.")
        ansible_module.exit_json(changed=False,
                                 server_already_configured=True)

    client_fstore = sysrestore.FileStore(paths.IPA_CLIENT_SYSRESTORE)
    if client_fstore.has_files():
        options._installation_cleanup = False
        ansible_module.log(
            "IPA client is already configured on this system. "
            "Please uninstall it before configuring the IPA server.")
        ansible_module.exit_json(changed=False,
                                 client_already_configured=True)

    # validate reverse_zones
    if not options.allow_zone_overlap:
        for zone in options.reverse_zones:
            with redirect_stdout(ansible_log):
                check_zone_overlap(zone)

    # validate zonemgr
    if options.zonemgr:
        if six.PY3:
            with redirect_stdout(ansible_log):
                bindinstance.validate_zonemgr_str(options.zonemgr)
        else:
            try:
                # IDNA support requires unicode
                encoding = getattr(sys.stdin, 'encoding', None)
                if encoding is None:
                    encoding = 'utf-8'
                if not isinstance(value, unicode):
                    value = options.zonemgr.decode(encoding)
                else:
                    value = options.zonemgr
                with redirect_stdout(ansible_log):
                    bindinstance.validate_zonemgr_str(value)
            except ValueError as e:
                # FIXME we can do this in better way
                # https://fedorahosted.org/freeipa/ticket/4804
                # decode to proper stderr encoding
                stderr_encoding = getattr(sys.stderr, 'encoding', None)
                if stderr_encoding is None:
                    stderr_encoding = 'utf-8'
                error = unicode(e).encode(stderr_encoding)
                ansible_module.fail_json(msg=error)

    # external cert file paths are absolute
    if options.external_cert_files:
        for path in options.external_cert_files:
            if not os.path.isabs(path):
                ansible_module.fail_json(
                    msg="External cert file '%s' must use an absolute path" % path)

    options.setup_ca = True
    # We only set up the CA if the PKCS#12 options are not given.
    if options.dirsrv_cert_files and len(options.dirsrv_cert_files) > 0:
        options.setup_ca = False
    else:
        options.setup_ca = True

    if not options.setup_ca and options.ca_subject:
        ansible_module.fail_json(msg=
            "--ca-subject cannot be used with CA-less installation")
    if not options.setup_ca and options.subject_base:
        ansible_module.fail_json(msg=
            "--subject-base cannot be used with CA-less installation")
    if not options.setup_ca and options.setup_kra:
        ansible_module.fail_json(msg=
            "--setup-kra cannot be used with CA-less installation")

    # This will override any settings passed in on the cmdline
    if os.path.isfile(paths.ROOT_IPA_CACHE):
        # dm_password check removed, checked already
        try:
            cache_vars = read_cache(options.dm_password)
            options.__dict__.update(cache_vars)
            if cache_vars.get('external_ca', False):
                options.external_ca = False
                options.interactive = False
        except Exception as e:
            ansible_module.fail_json(msg="Cannot process the cache file: %s" % str(e))

    # ca_subject
    if options.ca_subject:
        ca.subject_validator(ca.VALID_SUBJECT_ATTRS, options.ca_subject)

    # IPv6 and SELinux check

    tasks.check_ipv6_stack_enabled()
    tasks.check_selinux_status()
    if check_ldap_conf is not None:
        check_ldap_conf()

    _installation_cleanup = True
    if not options.external_ca and not options.external_cert_files and \
       is_ipa_configured():
        _installation_cleanup = False
        ansible_module.fail_json(msg="IPA server is already configured on this system.")

    if not options.no_ntp:
        try:
            timeconf.check_timedate_services()
        except timeconf.NTPConflictingService as e:
            ansible_module.log(
                "WARNING: conflicting time&date synchronization service "
                "'%s' will be disabled in favor of chronyd" % \
                e.conflicting_service)
        except timeconf.NTPConfigurationError:
            pass

    if hasattr(httpinstance, "httpd_443_configured"):
        # Check to see if httpd is already configured to listen on 443
        if httpinstance.httpd_443_configured():
            ansible_module.fail_json(msg="httpd is already configured to listen on 443.")

    if not options.external_cert_files:
        # Make sure the 389-ds ports are available
        try:
            check_dirsrv(True)
        except ScriptError as e:
            ansible_module.fail_json(msg=e)

    # check bind packages are installed
    if options.setup_dns:
        # Don't require an external DNS to say who we are if we are
        # setting up a local DNS server.
        options.no_host_dns = True

    # host name
    if options.host_name:
        host_default = options.host_name
    else:
        host_default = get_fqdn()

    try:
        verify_fqdn(host_default, options.no_host_dns)
        host_name = host_default
    except BadHostError as e:
        ansible_module.fail_json(msg=e)

    host_name = host_name.lower()

    if not options.domain_name:
        domain_name = host_name[host_name.find(".")+1:]
        try:
            validate_domain_name(domain_name)
        except ValueError as e:
            ansible_module.fail_json(msg="Invalid domain name: %s" % unicode(e))
    else:
        domain_name = options.domain_name

    domain_name = domain_name.lower()

    if not options.realm_name:
        realm_name = domain_name.upper()
    else:
        realm_name = options.realm_name.upper()

    argspec = inspect.getargspec(validate_domain_name)
    if "entity" in argspec.args:
        # NUM_VERSION >= 40690:
        try:
            validate_domain_name(realm_name, entity="realm")
        except ValueError as e:
            raise ScriptError("Invalid realm name: {}".format(unicode(e)))

    if not options.setup_adtrust:
        # If domain name and realm does not match, IPA server will not be able
        # to establish trust with Active Directory. Fail.

        if domain_name.upper() != realm_name:
            ansible_module.warn(
                "Realm name does not match the domain name: "
                "You will not be able to establish trusts with Active "
                "Directory.")

    # Do not ask for time source
    #if not options.no_ntp and not options.unattended and not (
    #        options.ntp_servers or options.ntp_pool):
    #    options.ntp_servers, options.ntp_pool = timeconf.get_time_source()

    #########################################################################

    http_pkcs12_file = None
    http_pkcs12_info = None
    http_ca_cert = None
    dirsrv_pkcs12_file = None
    dirsrv_pkcs12_info = None
    dirsrv_ca_cert = None
    pkinit_pkcs12_file = None
    pkinit_pkcs12_info = None
    pkinit_ca_cert = None

    if options.http_cert_files:
        if options.http_pin is None:
            ansible_module.fail_json(msg=
                "Apache Server private key unlock password required")
        http_pkcs12_file, http_pin, http_ca_cert = load_pkcs12(
            cert_files=options.http_cert_files,
            key_password=options.http_pin,
            key_nickname=options.http_cert_name,
            ca_cert_files=options.ca_cert_files,
            host_name=host_name)
        http_pkcs12_info = (http_pkcs12_file.name, http_pin)

    if options.dirsrv_cert_files:
        if options.dirsrv_pin is None:
            ansible_module.fail_json(msg=
                "Directory Server private key unlock password required")
        dirsrv_pkcs12_file, dirsrv_pin, dirsrv_ca_cert = load_pkcs12(
            cert_files=options.dirsrv_cert_files,
            key_password=options.dirsrv_pin,
            key_nickname=options.dirsrv_cert_name,
            ca_cert_files=options.ca_cert_files,
            host_name=host_name)
        dirsrv_pkcs12_info = (dirsrv_pkcs12_file.name, dirsrv_pin)

    if options.pkinit_cert_files:
        if options.pkinit_pin is None:
            ansible_module.fail_json(msg=
                "Kerberos KDC private key unlock password required")
        pkinit_pkcs12_file, pkinit_pin, pkinit_ca_cert = load_pkcs12(
            cert_files=options.pkinit_cert_files,
            key_password=options.pkinit_pin,
            key_nickname=options.pkinit_cert_name,
            ca_cert_files=options.ca_cert_files,
            realm_name=realm_name)
        pkinit_pkcs12_info = (pkinit_pkcs12_file.name, pkinit_pin)

    if (options.http_cert_files and options.dirsrv_cert_files and
        http_ca_cert != dirsrv_ca_cert):
        ansible_module.fail_json(msg=
            "Apache Server SSL certificate and Directory Server SSL "
            "certificate are not signed by the same CA certificate")

    if (options.http_cert_files and options.pkinit_cert_files and
        http_ca_cert != pkinit_ca_cert):
        ansible_module.fail_json(msg=
            "Apache Server SSL certificate and PKINIT KDC "
            "certificate are not signed by the same CA certificate")

    # done ##################################################################

    ansible_module.exit_json(changed=False,
                             ipa_python_version=IPA_PYTHON_VERSION,
                             ### basic ###
                             domain=options.domain_name,
                             realm=realm_name,
                             hostname=host_name,
                             _hostname_overridden=bool(options.host_name),
                             no_host_dns=options.no_host_dns,
                             ### server ###
                             setup_adtrust=options.setup_adtrust,
                             setup_kra=options.setup_kra,
                             setup_ca=options.setup_ca,
                             idstart=options.idstart,
                             idmax=options.idmax,
                             no_pkinit=options.no_pkinit,
                             ### ssl certificate ###
                             _dirsrv_pkcs12_file=dirsrv_pkcs12_file,
                             _dirsrv_pkcs12_info=dirsrv_pkcs12_info,
                             _dirsrv_ca_cert=dirsrv_ca_cert,
                             _http_pkcs12_file=http_pkcs12_file,
                             _http_pkcs12_info=http_pkcs12_info,
                             _http_ca_cert=http_ca_cert,
                             _pkinit_pkcs12_file=pkinit_pkcs12_file,
                             _pkinit_pkcs12_info=pkinit_pkcs12_info,
                             _pkinit_ca_cert=pkinit_ca_cert,
                             ### certificate system ###
                             external_ca=options.external_ca,
                             external_ca_type=options.external_ca_type,
                             external_ca_profile=options.external_ca_profile,
                             ### ad trust ###
                             rid_base=options.rid_base,
                             secondary_rid_base=options.secondary_rid_base,
                             ### client ###
                             ntp_servers=options.ntp_servers,
                             ntp_pool=options.ntp_pool,
                             ### additional ###
                             _installation_cleanup=_installation_cleanup,
                             domainlevel=options.domainlevel)

if __name__ == '__main__':
    main()
