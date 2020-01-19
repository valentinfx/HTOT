#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module: htot.htot_OnCreated
:description: HtoT node 'OnCreated' callback script
    This file is just a copy of what's inside the HDA "Script" tab
:author: Valentin David <vdavid.pro@gmail.com>
:license: MIT License
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
    """HtoT node 'OnCreated' callback script

    This will check if the current machine can import the tractor module
    """
    try:
        import tractor

    except ImportError:
        errorMsg = 'Could not import tractor module, you wont be able to use HtoT until this is fixed\n' \
                   'You can try adding the Tractor API path to your PYTHONPATH environment variable'
        hou.ui.displayMessage(errorMsg, severity=hou.severityType.Error)
        return


onCreated()
