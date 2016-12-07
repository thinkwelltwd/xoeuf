#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xoeuf.api
# ---------------------------------------------------------------------
# Copyright (c) 2015-2016 Merchise and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2015-01-01

'''Odoo API bridge.

Eases the task of writing modules which are compatible with both Odoo and
OpenERP.

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

from xoutil.decorator.meta import decorator

try:
    from openerp.api import guess
except ImportError:
    # Try Odoo 10+
    from odoo.api import guess

try:
    from openerp.api import Environment
except ImportError:
    # Try Odoo 10+
    from odoo.api import Environment


def contextual(func):
    '''Decorate a function to run within a proper Odoo environment.

    You should decorate every function that represents an "entry point" for
    working with the ORM.  If Odoo is not installed, the original function is
    returned unchanged.  However, if Odoo is present a proper
    `Environment`:class: is entered upon calling the function.

    Every command in the `xoeuf.cli`:mod: is automatically decorated.

    '''
    def inner(*args, **kwargs):
        with Environment.manage():
            return func(*args, **kwargs)
    return inner


try:
    from openerp.api import v8, v7  # noqa
except ImportError:
    from odoo.api import v8, v7  # noqa

try:
    from openerp import api as _odoo_api
except ImportError:  # Odoo 10+
    from odoo import api as _odoo_api
multi = _odoo_api.multi


@decorator
def take_one(func, index=0, warn=True):
    '''A weaker version of `api.one`.

    The decorated method will receive a recordset with a single record
    just like `api.one` does.

    The single record will be the one in the `index` provided in the
    decorator.

    This means the decorated method *can* make the same assumptions about
    its `self` it can make when decorated with `api.one`.  Nevertheless
    its return value *will not* be enclosed in a list.

    If `warn` is True and more than one record is in the record set, a
    warning will be issued.

    If the given recordset has no `index`, raise an IndexError.

    '''
    from functools import wraps
    from xoutil import logger

    @multi
    @wraps(func)
    def inner(self):
        if self[index] != self:
            # More than one item was in the recordset.
            if warn:
                logger.warn('More than one record for function %s',
                            func, extra=self)
            self = self[index]
        return func(self)
    return inner
