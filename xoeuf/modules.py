# -*- encoding: utf-8 -*-
# ---------------------------------------------------------------------
# xoeuf.modules
# ---------------------------------------------------------------------
# Copyright (c) 2014-2017 Merchise Autrement [~º/~] and Contributors
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the LICENCE attached (see LICENCE file) in the distribution
# package.
#
# Created on 2014-04-28

'''External OpenERP's addons

'''

from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        absolute_import as _py3_abs_import)

import logging
import re

from xoutil.functools import lru_cache
from xoutil.modules import customize
from xoutil.modules import modulemethod

try:
    import openerp as _o  # noqa
    _ADDONS_NAMESPACE = re.compile(r'^openerp\.addons\.(?P<module>[^\.]+)\.')
except ImportError:  # Odoo 10+
    _ADDONS_NAMESPACE = re.compile(r'^odoo\.addons\.(?P<module>[^\.]+)\.')

XOEUF_EXTERNAL_ADDON_GROUP = 'xoeuf.addons'


class _PatchesRegistry(object):
    _registry = {}
    _wrapped = {}

    def __call__(self, func):
        from xoutil.names import nameof
        name = nameof(func, inner=True, full=False)
        self._registry[name] = func
        return func

    def get_super(self, name):
        return self._wrapped[name]

    def apply(self):
        try:
            from openerp.modules import module
        except ImportError:
            from odoo.modules import module
        patched = getattr(module, '__xoeuf_patched__', False)
        if patched:
            # This is an Odoo that's being patched by us.
            return
        bootstraped = getattr(self, 'bootstraped', False)
        if not bootstraped:
            for name, func in self._registry.items():
                self._wrapped[name] = getattr(module, name)
            module = customize(module)[0]
            for name, func in self._registry.items():
                setattr(module, name, func)
            self.bootstraped = True

patch = _PatchesRegistry()


@modulemethod
@lru_cache(1)
def find_external_addons(self):
    '''Finds all externally installed addons.

    Externally installed addons are modules that are distributed with
    setuptools' distributions.

    An externally addon is defined in a package that defines an `entry
    point`__ in the group "xoeuf.addons" which points to a standard package
    (i.e loadable without any specific loader).

    :returns:  A dictionary from addons to it's a tuple of `(container's path,
               entry_point)`.

    Example::

       [xoeuf.addons]
       xopgi_account = xopgi.addons.xopgi_account

    '''
    import os
    from pkg_resources import iter_entry_points
    from xoutil.iterators import delete_duplicates
    res = []
    for entry in iter_entry_points(XOEUF_EXTERNAL_ADDON_GROUP):
        if not entry.attrs:
            # The entry-point is a whole module.  We can't load the module
            # here, cause the whole point is to grab the paths before openerp
            # is configured, but if you load an OpenERP addon you will be
            # importing openerp somehow and enacting configuration
            loc = entry.dist.location
            relpath = entry.module_name.replace('.', os.path.sep)
            # The parent directory is the one!
            abspath = os.path.abspath(os.path.join(loc, relpath, '..'))
            if os.path.isdir(abspath):
                res.append(abspath)
                name = entry.module_name
                pos = name.rfind('.')
                if pos >= 0:
                    name = name[pos+1:]
    return delete_duplicates(res)


@patch
@modulemethod
def initialize_sys_path(self):
    from xoutil.objects import setdefaultattr
    try:
        from openerp.modules import module
    except ImportError:
        from odoo.modules import module
    _super = patch.get_super('initialize_sys_path')
    external_addons = setdefaultattr(self, '__addons', [])
    if not external_addons:
        _super()
        result = module.ad_paths
        external_addons.extend(self.find_external_addons())
        result.extend(external_addons)
        module.ad_paths = result
        return result
    else:
        return module.ad_paths


def patch_modules():
    '''Patches OpenERP `modules.module` to work with external addons.

    '''
    patch.apply()


def _get_registry(db_name):
    '''Helper method to get the registry for a `db_name`.'''
    from xoutil.eight import string_types
    try:
        from odoo.modules.registry import Registry
        get_registry = Registry
    except ImportError:
        from openerp.modules.registry import Registry, RegistryManager
        get_registry = RegistryManager.get
    if isinstance(db_name, string_types):
        db = get_registry(db_name)
    elif isinstance(db_name, Registry):
        db = db_name
    else:
        import sys
        caller = sys.getframe(1).f_code.co_name
        raise TypeError('"%s" requires a string or a Registry' % caller)
    return db


def get_dangling_modules(db):
    '''Get registered modules that are no longer available.

    Returns the list of dangling modules.  Each item in the list the `read` of
    the `ir.module.module`.

    A dangling module is one that is listed in the instances DB, but is not
    reachable in any of the addons paths (not even externally installed).

    :param db: Either the name of the database to load or a `registry
               <xoeuf.osv.registry.Registry>`:class:.

    '''
    try:
        from openerp import SUPERUSER_ID
        from openerp.modules.module import get_modules
    except ImportError:
        from odoo import SUPERUSER_ID
        from odoo.modules.module import get_modules
    from xoeuf.osv.model_extensions import search_read
    registry = _get_registry(db)
    with registry.cursor() as cr:
        ir_modules = registry['ir.module.module']
        available = get_modules()
        dangling = search_read(ir_modules, cr, SUPERUSER_ID,
                               [('name', 'not in', available)],
                               context=None, ensure_list=True)
        return dangling


def mark_dangling_modules(db):
    '''Mark `dangling <get_dangling_modules>`:func: as uninstallable.

    Parameters and return value are the same as in function
    :func:`get_dangling_modules`.

    '''
    try:
        from openerp import SUPERUSER_ID
    except ImportError:
        from odoo import SUPERUSER_ID
    from xoeuf.osv.model_extensions import get_writer
    registry = _get_registry(db)
    with registry.cursor() as cr:
        ir_mods = registry['ir.module.module']
        dangling = get_dangling_modules(registry)  # reuse the registry
        dangling_ids = [module['id'] for module in dangling]
        with get_writer(ir_mods, cr, SUPERUSER_ID, dangling_ids) as writer:
            writer.update(state='uninstallable')
        return dangling


def get_object_module(obj, typed=False):
    '''Return the name of the OpenERP addon the `obj` has been defined.

    If the `obj` is not defined (imported) from the "openerp.addons."
    namespace, return None.

    '''
    from xoutil.names import nameof
    name = nameof(obj, inner=True, full=True, typed=typed)
    match = _ADDONS_NAMESPACE.match(name)
    if match:
        module = match.group(1)
        return module
    else:
        return None


del re, logging
