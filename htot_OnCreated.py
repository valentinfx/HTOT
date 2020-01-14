#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module:
:description:
:author: Valentin David <vdavid.pro@gmail.com>
:maintainer:
"""
# --------------------------------------------------------------------------------------------------
# Python built-in modules import
# --------------------------------------------------------------------------------------------------
import os
import logging as log

# --------------------------------------------------------------------------------------------------
# Third-party modules import
# --------------------------------------------------------------------------------------------------
import hou

# --------------------------------------------------------------------------------------------------
# Globals
# --------------------------------------------------------------------------------------------------
log.basicConfig(level='DEBUG')

# --------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------


def onCreated():
    """HtoT node 'onCreated' callback script

    This will check if the Tractor API path was found in PYTHONPATH environment variable
    """
    errorMsg = 'Tractor API path was not found in PYTHONPATH environment variable. \n' \
               'You wont be able to use HtoT until this is fixed.'

    try:
        pythonPaths = os.environ['PYTHONPATH'].split(os.pathsep)

    except KeyError:
        hou.ui.displayMessage(errorMsg, severity=hou.severityType.Error)
        return

    tractorApiPath = [path for path in pythonPaths if 'Tractor-2.3/lib/python2.7/Lib/site-packages' in path]

    if not tractorApiPath:
        hou.ui.displayMessage(errorMsg, severity=hou.severityType.Error)
        return

    # log.debug('tractorApiPath : {}'.format(tractorApiPath))


onCreated()
