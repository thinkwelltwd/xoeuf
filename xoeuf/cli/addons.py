#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xoeuf.cli.addons
# ---------------------------------------------------------------------
# Copyright (c) 2015-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-04-07

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from . import Command


class Addons(Command):
    '''List all non-uninstallable addons found in the DB.

    '''
    @classmethod
    def get_arg_parser(cls):
        res = getattr(cls, '_arg_parser', None)
        if not res:
            from argparse import ArgumentParser
            res = ArgumentParser()
            cls._arg_parser = res
            res.add_argument('-f', '--filter',
                             dest='filters',
                             default=[],
                             action='append')
        return res

    @classmethod
    def database_factory(cls, database):
        import importlib
        module = 'xoeuf.pool.%s' % database
        return importlib.import_module(module)

    def run(self, args=None):
        parser = self.get_arg_parser()
        options = parser.parse_args(args)
        filters = options.filters
        self.list_addons(filters)

    def list_addons(self, filters):
        addons = self.get_addons(filters)
        for addon in addons:
            print(addon)

    def get_addons(self, filters):
        try:
            from openerp.modules import get_modules
        except ImportError:
            from odoo.modules import get_modules
        return [
            addon
            for addon in get_modules()
            if not filters or any(addon.startswith(f) for f in filters)
        ]
