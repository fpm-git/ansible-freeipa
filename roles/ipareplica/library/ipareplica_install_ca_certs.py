#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors:
#   Thomas Woerner <twoerner@redhat.com>
#
# Based on ipa-replica-install code
#
# Copyright (C) 2018  Red Hat
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

from __future__ import print_function

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview'],
}

DOCUMENTATION = '''
---
module: ipareplica_install_ca_cert
short description: Install CA certs
description:
  Install CA certs
options:
  dm_password:
    description: Directory Manager password
    required: yes
  password:
    description: Admin user kerberos password
    required: yes
  ip_addresses:
    description: List of Master Server IP Addresses
    required: no
  domain:
    description: Primary DNS domain of the IPA deployment
    required: yes
  realm:
    description: Kerberos realm name of the IPA deployment
    required: yes
  hostname:
    description: Fully qualified name of this host
    required: yes
  ca_cert_files:
    description: List of iles containing CA certificates for the service certificate files
    required: yes
  no_host_dns:
    description: Do not use DNS for hostname lookup during installation
    required: yes
  setup_adtrust:
    description: 
    required: yes
  setup_kra:
    description: 
    required: yes
  setup_dns:
    description: 
    required: yes
  external_ca:
    description: 
    required: yes
  external_cert_files:
    description: 
    required: yes
  subject_base:
    description: 
    required: yes
  ca_subject:
    description: 
    required: yes
  setup_ca:
    description: 
    required: yes
  _hostname_overridden:
    description: 
    required: yes
author:
    - Thomas Woerner
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_ipa_replica import (
    AnsibleModuleLog, installer, DN, paths,
    ansible_module_get_parsed_ip_addresses,
    gen_env_boostrap_finalize_core, constants, api_bootstrap_finalize,
    gen_ReplicaConfig, gen_remote_api, api, redirect_stdout, ipaldap,
    install_ca_cert
)

def main():
    ansible_module = AnsibleModule(
        argument_spec = dict(
            ### basic ###
            dm_password=dict(required=False, no_log=True),
            password=dict(required=False, no_log=True),
            ip_addresses=dict(required=False, type='list', default=[]),
            domain=dict(required=False),
            realm=dict(required=False),
            hostname=dict(required=False),
            ca_cert_files=dict(required=False, type='list', default=[]),
            no_host_dns=dict(required=False, type='bool', default=False),
            ### server ###
            setup_adtrust=dict(required=False, type='bool'),
            setup_ca=dict(required=False, type='bool'),
            setup_kra=dict(required=False, type='bool'),
            setup_dns=dict(required=False, type='bool'),
            ### ssl certificate ###
            dirsrv_cert_files=dict(required=False, type='list', default=[]),
            ### client ###
            force_join=dict(required=False, type='bool'),
            ### certificate system ###
            subject_base=dict(required=True),
            ### additional ###
            server=dict(required=True),
            ccache=dict(required=True),
            installer_ccache=dict(required=True),
            _top_dir = dict(required=True),
            _add_to_ipaservers = dict(required=True, type='bool'),
            _ca_subject=dict(required=True),
            _subject_base=dict(required=True),
            dirman_password=dict(required=True, no_log=True),
            config_setup_ca=dict(required=True, type='bool'),
            config_master_host_name=dict(required=True),
            config_ca_host_name=dict(required=True),
            config_ips=dict(required=False, type='list', default=[]),
        ),
        supports_check_mode = True,
    )

    ansible_module._ansible_debug = True
    ansible_log = AnsibleModuleLog(ansible_module)

    # get parameters #

    options = installer
    ### basic ###
    options.dm_password = ansible_module.params.get('dm_password')
    options.password = options.dm_password
    options.admin_password = ansible_module.params.get('password')
    options.ip_addresses = ansible_module_get_parsed_ip_addresses(
        ansible_module)
    options.domain_name = ansible_module.params.get('domain')
    options.realm_name = ansible_module.params.get('realm')
    options.host_name = ansible_module.params.get('hostname')
    options.ca_cert_files = ansible_module.params.get('ca_cert_files')
    options.no_host_dns = ansible_module.params.get('no_host_dns')
    ### server ###
    options.setup_adtrust = ansible_module.params.get('setup_adtrust')
    options.setup_ca = ansible_module.params.get('setup_ca')
    options.setup_kra = ansible_module.params.get('setup_kra')
    options.setup_dns = ansible_module.params.get('setup_dns')
    ### ssl certificate ###
    options.dirsrv_cert_files = ansible_module.params.get('dirsrv_cert_files')
    ### client ###
    options.force_join = ansible_module.params.get('force_join')
    ### certificate system ###
    options.external_ca = ansible_module.params.get('external_ca')
    options.external_cert_files = ansible_module.params.get(
        'external_cert_files')
    options.subject_base = ansible_module.params.get('subject_base')
    if options.subject_base is not None:
        options.subject_base = DN(options.subject_base)
    options.ca_subject = ansible_module.params.get('ca_subject')
    ### additional ###
    options.server = ansible_module.params.get('server')
    ccache = ansible_module.params.get('ccache')
    os.environ['KRB5CCNAME'] = ccache
    #os.environ['KRB5CCNAME'] = ansible_module.params.get('installer_ccache')
    installer._ccache = ansible_module.params.get('installer_ccache')
    options.subject_base = ansible_module.params.get('subject_base')
    if options.subject_base is not None:
        options.subject_base = DN(options.subject_base)
    options._top_dir = ansible_module.params.get('_top_dir')
    options._add_to_ipaservers = ansible_module.params.get('_add_to_ipaservers')
    options._ca_subject = ansible_module.params.get('_ca_subject')
    options._subject_base = ansible_module.params.get('_subject_base')
    dirman_password = ansible_module.params.get('dirman_password')
    config_setup_ca = ansible_module.params.get('config_setup_ca')
    config_master_host_name = ansible_module.params.get('config_master_host_name')
    config_ca_host_name = ansible_module.params.get('config_ca_host_name')
    config_ips = ansible_module_get_parsed_ip_addresses(ansible_module,
                                                        "config_ips")

    # init #

    ansible_log.debug("== INSTALLER ==")

    options = installer
    promote = installer.promote

    env = gen_env_boostrap_finalize_core(paths.ETC_IPA,
                                         constants.DEFAULT_CONFIG)
    api_bootstrap_finalize(env)
    config = gen_ReplicaConfig()
    config.dirman_password = dirman_password
    config.setup_ca = config_setup_ca
    config.master_host_name = config_master_host_name
    config.ca_host_name = config_ca_host_name
    config.ips = config_ips

    remote_api = gen_remote_api(config.master_host_name, paths.ETC_IPA)
    installer._remote_api = remote_api

    conn = remote_api.Backend.ldap2
    ccache = os.environ['KRB5CCNAME']

    cafile = paths.IPA_CA_CRT
    with redirect_stdout(ansible_log):
        try:
            ansible_log.debug("-- CONNECT --")
            if promote:
                conn.connect(ccache=ccache)
            else:
                # dmlvl 0 replica install should always use DM credentials
                # to create remote LDAP connection. Since ACIs permitting hosts
                # to manage their own services were added in 4.2 release,
                # the master denies this operations.
                conn.connect(bind_dn=ipaldap.DIRMAN_DN, cacert=cafile,
                             bind_pw=dirman_password)

            ansible_log.debug("-- INSTALL_CA_CERT --")
            # Update and istall updated CA file
            cafile = install_ca_cert(conn, api.env.basedn, api.env.realm, cafile)
            install_ca_cert(conn, api.env.basedn, api.env.realm, cafile,
                            destfile=paths.KDC_CA_BUNDLE_PEM)
            install_ca_cert(conn, api.env.basedn, api.env.realm, cafile,
                            destfile=paths.CA_BUNDLE_PEM)

        finally:
            if conn.isconnected():
                ansible_log.debug("-- DISCONNECT --")
                conn.disconnect()

    # done #

    ansible_module.exit_json(changed=True,
                             config_master_host_name=config.master_host_name,
                             config_ca_host_name=config.ca_host_name)

if __name__ == '__main__':
    main()
