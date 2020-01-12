#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module: htot
:version: v2.0.0
:description: Core functions for HDA module that allows spooling jobs to Tractor
    This file is just a copy of what's inside the HDA "Script" tab
:author: Valentin David <vdavid.pro@gmail.com>
:license: MIT License
"""
# --------------------------------------------------------------------------------------------------
# Python built-in modules import
# --------------------------------------------------------------------------------------------------
import os
import sys
import logging as log

# --------------------------------------------------------------------------------------------------
# Third-party modules import
# --------------------------------------------------------------------------------------------------
import hou
import tractor.api.author as author

# --------------------------------------------------------------------------------------------------
# Globals
# --------------------------------------------------------------------------------------------------
log.basicConfig(level='DEBUG')  # TODO : switch to info before merge

NODE = hou.pwd

TRACTOR_API_PATH = NODE.evalParm('tractorApiPath') or 'C:/Program Files/Pixar/Tractor-2.3'
TRACTOR_URL = NODE.evalParm('tractorUrl') or 'http://tractor-engine/tv/'
# TEMP_DIR = NODE.evalParm('tempDir') or hou.expandString('$HIP/rfhTemp')

HOUDINI_BIN = os.path.join(hou.expandString('$HFS'), 'bin')


# --------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------


# TODO : refacto in a class


def checkUnsavedChanges():
    """This will check if the current scene has unsaved changes"""
    if hou.hipFile.hasUnsavedChanges():
        text = 'Current scene has unsaved changes. Cannot send to farm'
        hou.ui.displayMessage(text, severity=hou.severityType.Warning)
        return True

    else:
        return False


def addToPathEnvVar():
    """Add Tractor API and Houdini bin paths to the 'Path' environment variable"""
    if TRACTOR_API_PATH not in sys.path:
        log.info('Adding to "Path" environment variable : \n{}'.format(TRACTOR_API_PATH))
        sys.path.append(TRACTOR_API_PATH)

    if HOUDINI_BIN not in sys.path:
        log.info('Adding to "Path" environment variable : \n{}'.format(HOUDINI_BIN))
        sys.path.append(HOUDINI_BIN)


def evaluateNode():
    """Evaluate houdini node parameters to get job arguments
    :return: A tuple of needed arguments to create the tractor job
    :rtype: tuple
    """
    # Fetch node's parameters values
    renderNode = NODE.evalParm('renderNode')

    # We need to raise an error if the node does not exist
    if not hou.node(renderNode):
        text = 'Node "{}" does not exist, aborting'.format(renderNode)
        hou.ui.displayMessage(text, severity=hou.severityType.Error)

    start = NODE.evalParm('rangex') or hou.expandString('$FSTART')
    end = NODE.evalParm('rangey') or hou.expandString('$FEND')
    shotName = NODE.evalParm('shotName') or hou.expandString('$HIPNAME')
    project = NODE.evalParm('project') or ''
    priority = NODE.evalParm('priority') or 1
    maxActive = NODE.evalParm('maxActive') or 0
    renderPath = NODE.evalParm('renderPath') or hou.expandString('$HIP/render')
    debugMode = NODE.evalParm('debugMode')

    service = NODE.evalParm('service') or 'PixarRender'

    # cast to needed types (XXX note sure this is needed)
    # start = int(start)
    # end = int(end)
    # priority = int(priority)

    jobTitle = '[{}] Render frames {} - {}'.format(shotName.strip('.hip'), start, end)

    return renderNode, start, end, jobTitle, project, priority, service


def createPaths(paths):
    """This will create the needed paths if they don't exist
    :param paths: The paths to create
    :type paths: str | list of str
    """
    if isinstance(basestring, paths):
        paths = [paths]

    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)


def createJob(renderNode, start, end, jobTitle, service, project, priority):
    """Create a Renderman for Houdini tractor job

    :param renderNode: absolute path to the node to render
    :type renderNode: str
    :param start: start frame
    :type start: int
    :param end: end frame
    :type end: int
    :param jobTitle: Title for the job
    :type jobTitle: str
    :param project: Current project name
    :type project: str
    :param priority: Job priority
    :type priority: int
    :param service: Job and tasks Service
    :type service: str
    :return: A Tractor Job object
    :rtype: :class:`tractor.api.author.Job`
    """
    sceneFile = hou.hipFile.path()

    # Create job
    jobInstance = author.Job(title=jobTitle, projects=[project], priority=priority, service=service)

    # Create one task per frame
    for frame in range(start, end + 1):
        taskTitle = 'Render frame {}'.format(frame)
        # jobInstance.newTask(title=taskTitle, argv=['/usr/bin/prman', 'file.rib'], service=service)
        hbatchPath = os.path.join(HOUDINI_BIN, 'hbatch.exe')
        cmd = 'e render -V -f {0} {1} {2} ; quit'.format(frame, frame, renderNode)
        jobInstance.newTask(title=taskTitle, argv=['', cmd, sceneFile], service=service)

    return jobInstance


def sendToFarm(jobInstance, debugMode=True):
    """Send job to farm

    :param jobInstance: The job to send to the farm
    :type jobInstance: :class:`tractor.api.author.Job`
    :param debugMode: If True, will only print the job dictionary
    :type debugMode: bool
    """
    if debugMode:
        log.info('Job to send : \n')
        print jobInstance.asTcl()
    else:
        jobId = jobInstance.spool()
        log.info('Job sent to farm : {}#jid={}'.format(TRACTOR_URL, jobId))


def run():
    """HDA 'Send To Farm' button callback script"""
    if checkUnsavedChanges():
        return

    addToPathEnvVar()
    jobArgs = evaluateNode()
    job = createJob(*jobArgs)
    sendToFarm(job, debugMode=True)
