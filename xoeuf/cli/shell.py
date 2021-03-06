# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xoeuf.cli.shell
# ---------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2014-05-02


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)


import code
import logging
import os
import signal
import sys

try:
    import odoo
    from odoo.tools import config
except ImportError:
    import openerp as odoo
    from openerp.tools import config

from xoeuf.api import contextual
from xoutil.eight.types import new_class

from . import Command

_logger = logging.getLogger(__name__)


def raise_keyboard_interrupt(*a):
    raise KeyboardInterrupt()


class Console(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>"):
        code.InteractiveConsole.__init__(self, locals, filename)
        try:
            import readline
            import rlcompleter
        except ImportError:
            print('readline or rlcompleter not available, '
                  'autocomplete disabled.')
        else:
            readline.set_completer(rlcompleter.Completer(locals).complete)
            readline.parse_and_bind("tab: complete")


class Base(object):
    # This Base is just here to have many 'shell' commands.  See aliases
    # below.  Odoo 9 includes its own 'shell' command, we the aliases to be
    # able to work with our shell.
    #
    # In fact, this is a backport of Odoo 10 shell command into xoeuf, so that
    # our shell for Odoo 8, behaves the same as theirs.
    supported_shells = ['ipython', 'ptpython', 'bpython', 'python']

    def init(self, args):
        config.parse_config(args)
        odoo.cli.server.report_configuration()
        odoo.service.server.start(preload=[], stop=True)
        signal.signal(signal.SIGINT, raise_keyboard_interrupt)

    def console(self, local_vars):
        if not os.isatty(sys.stdin.fileno()):
            exec sys.stdin in local_vars
        else:
            if 'env' not in local_vars:
                print(
                    'No environment set, use `%s shell -d dbname` '
                    'to get one.' % sys.argv[0]
                )
            for i in sorted(local_vars):
                print('%s: %s' % (i, local_vars[i]))

            preferred_interface = config.options.get('shell_interface')
            if preferred_interface:
                shells_to_try = [preferred_interface, 'python']
            else:
                shells_to_try = self.supported_shells

            for shell in shells_to_try:
                try:
                    return getattr(self, shell)(local_vars)
                except ImportError:
                    pass
                except Exception:
                    _logger.warning("Could not start '%s' shell." % shell)
                    _logger.debug("Shell error:", exc_info=True)

    def ipython(self, local_vars):
        from IPython import start_ipython
        start_ipython(argv=[], user_ns=local_vars)

    def ptpython(self, local_vars):
        from ptpython.repl import embed
        embed({}, local_vars)

    def bpython(self, local_vars):
        from bpython import embed
        embed(local_vars)

    def python(self, local_vars):
        Console(locals=local_vars).interact()

    def shell(self, dbname):
        local_vars = {
            'openerp': odoo,
            'odoo': odoo,
        }
        if dbname:
            registry = odoo.registry(dbname)
            with registry.cursor() as cr:
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
                env = odoo.api.Environment(cr, uid, ctx)
                local_vars['env'] = env
                local_vars['self'] = env.user
                self.console(local_vars)
        else:
            self.console(local_vars)

    @contextual
    def run(self, args):
        self.init(args)
        self.shell(config['db_name'])
        return 0


for alias in ('shell', 'ishell', 'python', 'ipython'):
    class aliased(object):
        command_cli_name = alias

    def exec_body(d):
        d['__doc__'] = 'A shell for Odoo'
        return d

    globals()[alias] = new_class(alias, (aliased, Base, Command), exec_body=exec_body)
