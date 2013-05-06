#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------
# setup
#----------------------------------------------------------------------
# Copyright (c) 2013 Merchise Autrement
# All rights reserved.
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License (GPL) as published by the
# Free Software Foundation;  either version 2  of  the  License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
# Created on 2013-05-05


from __future__ import (division as _py3_division,
                        print_function as _py3_print,
                        unicode_literals as _py3_unicode)
                        # XXX: Don't put absolute imports in setup.py

import sys, os
from setuptools import setup, find_packages

# Import the version from the release module
project_name = 'xoeuf'
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_current_dir, project_name))
from release import VERSION as version

setup(name=project_name,
      version=version,
      description="Basic utilities for OpenERP Open Object Services",
      long_description=open(os.path.join('docs', 'readme.txt')).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
      ],
      keywords='openerp open-object server library',
      author='Merchise Autrement',
      author_email='',
      url='http://www.merchise.org/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'xoutil',
      ],
      extra_requires={
        # If you really need Xotl it's best to move it to install_requires
        'xotl2': ['xotl>=2.1.11,<3', ],
        'xotl3': ['xotl>=3.0.0', ],
        'doc': ['docutils>=0.7', 'Sphinx>=1.0.7', ]
      },
      entry_points="""

      """,
      )
