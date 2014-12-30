# -*- encoding: utf-8 -*-
#----------------------------------------------------------------------
# xoeuf.cli.secure
#----------------------------------------------------------------------
# Copyright (c) 2014 Merchise Autrement and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2014-12-04

'''Secures a DB by:

- Changing all passwords

- [TODO] Changing all accounting related data by a random mapping.

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from . import Command


class Secure(Command):
    '''The secure command.

    '''

    @classmethod
    def get_arg_parser(cls):
        def path(extensions=None):
            '''A type-builder for file arguments.'''
            from xoutil.types import is_collection
            from os.path import abspath, isfile, splitext
            if extensions and not is_collection(extensions):
                extensions = (extensions, )
            acceptable = lambda ext: not extensions or ext in extensions

            def inner(value):
                res = abspath(value)
                name, extension = splitext(value)
                if not isfile(res) or not acceptable(extension):
                    raise TypeError('Invalid filename %r' % res)
                return res
            return inner

        res = getattr(cls, '_arg_parser', None)
        if not res:
            from argparse import ArgumentParser
            res = ArgumentParser()
            cls._arg_parser = res
            res.add_argument('-c', '--config', dest='conf',
                             required=False,
                             default=None,
                             type=path(),
                             help='A configuration file.  This could be '
                             'either a Python file, like that required by '
                             'Gunicorn deployments, or a INI-like '
                             'like the standard ".openerp-serverrc".')
            res.add_argument('-d', '--database', dest='database',
                             type=cls.database_factory,
                             required=True)
            loggroup = res.add_argument_group('Logging')
            loggroup.add_argument('--log-level',
                                  choices=('debug', 'warning',
                                           'info', 'error'),
                                  default='warning',
                                  help='How much to log')
        return res

    @classmethod
    def database_factory(cls, database):
        import importlib
        module = 'xoeuf.pool.%s' % database
        return importlib.import_module(module)

    def run(self, args=None):
        from xoeuf.security import reset_all_passwords
        parser = self.get_arg_parser()
        options = parser.parse_args(args)
        conffile = options.conf
        if conffile:
            self.read_conffile(conffile)
        db = options.database
        reset_all_passwords(db, security_level='basic')

    def read_conffile(self, filename):
        import os
        ext = os.path.splitext(filename)[-1]
        if ext == '.py':
            self.load_config_from_script(filename)
        else:
            self.load_config_from_inifile(filename)

    @staticmethod
    def load_config_from_script(filename):
        from six import exec_
        cfg = {
            "__builtins__": __builtins__,
            "__name__": "__config__",
            "__file__": filename,
            "__doc__": None,
            "__package__": None
        }
        try:
            with open(filename, 'rb') as fh:
                return exec_(compile(fh.read(), filename, 'exec'), cfg, cfg)
        except Exception:
            import traceback, sys
            print("Failed to read config file: %s" % filename)
            traceback.print_exc()
            sys.exit(1)

    @staticmethod
    def load_config_from_inifile(filename):
        from openerp.tools import config
        config.rcfile = filename
        config.load()