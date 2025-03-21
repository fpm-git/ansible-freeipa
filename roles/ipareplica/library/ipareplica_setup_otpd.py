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
module: ipareplica_setup_otpd
short description: Setup OTPD
description:
  Setup OTPD
options:
  setup_ca:
    description: 
    required: yes
  setup_kra:
    description: 
    required: yes
  no_pkinit:
    description: 
    required: yes
  no_ui_redirect:
    description: 
    required: yes
  subject_base:
    description: 
    required: yes
  config_master_host_name:
    description: 
    required: yes
  ccache:
    description: 
    required: yes
  _ca_file:
    description: 
    required: yes
  _top_dir:
    description: 
    required: yes
  dirman_password:
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
    gen_env_boostrap_finalize_core, constants, api_bootstrap_finalize,
    gen_ReplicaConfig, gen_remote_api, api, redirect_stdout, otpdinstance,
    ipautil
)

def main():
    ansible_module = AnsibleModule(
        argument_spec = dict(
            #### server ###
            setup_ca=dict(required=False, type='bool'),
            setup_kra=dict(required=False, type='bool'),
            no_pkinit=dict(required=False, type='bool'),
            no_ui_redirect=dict(required=False, type='bool'),
            #### certificate system ###
            subject_base=dict(required=True),
            #### additional ###
            config_master_host_name=dict(required=True),
            ccache=dict(required=True),
            _ca_file=dict(required=False),
            _top_dir = dict(required=True),
            dirman_password=dict(required=True, no_log=True),
        ),
        supports_check_mode = True,
    )

    ansible_module._ansible_debug = True
    ansible_log = AnsibleModuleLog(ansible_module)

    # get parameters #

    options = installer
    options.setup_ca = ansible_module.params.get('setup_ca')
    options.setup_kra = ansible_module.params.get('setup_kra')
    options.no_pkinit = ansible_module.params.get('no_pkinit')
    ### certificate system ###
    options.subject_base = ansible_module.params.get('subject_base')
    if options.subject_base is not None:
        options.subject_base = DN(options.subject_base)
    ### additional ###
    master_host_name = ansible_module.params.get('config_master_host_name')
    ccache = ansible_module.params.get('ccache')
    os.environ['KRB5CCNAME'] = ccache
    #os.environ['KRB5CCNAME'] = ansible_module.params.get('installer_ccache')
    #installer._ccache = ansible_module.params.get('installer_ccache')
    options._top_dir = ansible_module.params.get('_top_dir')
    dirman_password = ansible_module.params.get('dirman_password')

    # init #

    ansible_log.debug("== INSTALL ==")

    options = installer

    env = gen_env_boostrap_finalize_core(paths.ETC_IPA,
                                         constants.DEFAULT_CONFIG)
    api_bootstrap_finalize(env)
    config = gen_ReplicaConfig()
    config.dirman_password = dirman_password

    remote_api = gen_remote_api(master_host_name, paths.ETC_IPA)

    conn = remote_api.Backend.ldap2
    ccache = os.environ['KRB5CCNAME']

    # There is a api.Backend.ldap2.connect call somewhere in ca, ds, dns or
    # ntpinstance
    api.Backend.ldap2.connect()
    conn.connect(ccache=ccache)

    with redirect_stdout(ansible_log):
        ansible_log.debug("-- INSTALL_OTPD --")

        otpd = otpdinstance.OtpdInstance()
        otpd.set_output(ansible_log)
        otpd.create_instance('OTPD', config.host_name,
                             ipautil.realm_to_suffix(config.realm_name))

    # done #

    ansible_module.exit_json(changed=True)

if __name__ == '__main__':
    main()
