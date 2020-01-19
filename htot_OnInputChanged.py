#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module: htot.htot_OnInputChanged
:description: HtoT node 'OnInputChanged' callback script
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


def onInputChanged():
    """Callback script executed every time the input connection is changed

    If the input connection is a Mantra or RIS node, this will link some parameters
    """
    node = kwargs.get('node')
    inputNode = node.inputs()[0]

    # outputDriverPath = inputNode.path()

    print inputNode


onInputChanged()


def onOutputDriverParmChange():
    """Callback script executed every time the 'outputDriver' parameter is changed

    If the outputDriver is a Mantra or RIS node, this will link some parameters
    """
    node = hou.pwd()
    outputDriverPath = node.evalParm('outputDriver')
    outputDriver = hou.node(outputDriverPath)

    # We need to return early to avoid slowing down Houdini too much
    if outputDriver is None:
        return

    outputDriverType = outputDriver.type().name()

    if outputDriverType not in NODE_TYPES_MAPPING.keys():
        return

    renderer = NODE_TYPES_MAPPING.get(outputDriverType)

    node.parm('rangex').setExpression('ch("{}/f1")'.format(outputDriverPath))
    node.parm('rangey').setExpression('ch("{}/f2")'.format(outputDriverPath))
    node.parm('renderer').set(renderer)