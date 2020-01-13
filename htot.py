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

# Feel free to change these
TRACTOR_API_PATH = 'C:/Program Files/Pixar/Tractor-2.3'
TRACTOR_URL = 'http://tractor-engine/tv/'
# TEMP_DIR = NODE.evalParm('tempDir') or hou.expandString('$HIP/rfhTemp')

HOUDINI_BIN = os.path.join(hou.expandString('$HFS'), 'bin')


# --------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------


class HtoTJob(object):
    """Defines a Houdini to Tractor job"""

    def __init__(self):
        """Evaluate HtoT node parameters to get job arguments"""
        self.sceneFile = hou.hipFile.path()
        self.node = hou.pwd()

        self.outputDriver = self.node.evalParm('outputDriver')
        self.outputDriverType = hou.node(self.node).type().name()

        # We need to raise an error if the output driver does not exist or is not of the right type
        if not hou.node(self.outputDriver):
            text = 'Node "{}" does not exist, aborting'.format(self.outputDriver)
            hou.ui.displayMessage(text, severity=hou.severityType.Error)

        if self.outputDriverType not in ['ifd', 'ris']:
            text = 'Node "{}" is of type "{}". Correct types are "ifd" (Mantra) ' \
                   'or "ris" (Renderman)'.format(self.outputDriver, self.outputDriverType)
            hou.ui.displayMessage(text, severity=hou.severityType.Error)

        self.renderer = 'Mantra' if self.outputDriverType == 'ifd' else 'RfH'

        # Evaluate "Job" tab parameters values
        self.start = self.node.evalParm('rangex') or hou.expandString('$FSTART')
        self.end = self.node.evalParm('rangey') or hou.expandString('$FEND')
        shotName = self.node.evalParm('shotName') or hou.expandString('$HIPNAME')
        projects = self.node.evalParm('projects') or ''
        self.projects = projects.replace(' ', '').split(',')
        self.priority = self.node.evalParm('priority') or 1
        self.maxActive = self.node.evalParm('maxActive') or 0
        self.debugMode = self.node.evalParm('debugMode')

        # Evaluate "Advanced" tab parameters values
        self.service = self.node.evalParm('service') or 'PixarRender'
        self.tractorApiPath = self.node.evalParm('tractorApiPath') or TRACTOR_API_PATH
        self.tractorUrl = self.node.evalParm('tractorUrl') or TRACTOR_URL

        # cast to needed types (XXX note sure this is needed)
        # start = int(start)
        # end = int(end)
        # priority = int(priority)

        # Construct job title
        self.jobTitle = '[{}][{}] Render frames {} - {}'.format(
            shotName.strip('.hip'),
            self.renderer,
            self.start,
            self.end
        )

        self.job = self.createJob()

    def createJob(self):
        """Create Houdini tractor job from parameters

        :return: A Tractor Job object
        :rtype: :class:`author.Job`
        """
        # Create job
        jobInstance = author.Job(
            title=self.jobTitle,
            projects=self.projects,
            priority=self.priority,
            service=self.service,
            maxActive=self.maxActive
        )

        # if self.outputDriverType == 'Mantra'  # TODO : generate ifd files

        # Create one task per frame
        for frame in range(self.start, self.end + 1):
            taskTitle = 'Render frame {}'.format(frame)
            hbatchPath = os.path.join(HOUDINI_BIN, 'hbatch.exe')
            cmd = '{0} e render -V -f {1} {2} {3} ; quit'.format(hbatchPath, frame, frame, self.outputDriver)
            jobInstance.newTask(title=taskTitle, argv=[cmd, self.sceneFile], service=self.service)

        return jobInstance

    def sendToFarm(self):
        """Send job to farm"""
        if self.debugMode:
            log.info('DEBUG MODE IS ON')
            log.info('Job to send : \n')
            print self.job.asTcl()
        else:
            jobId = self.job.spool()
            log.info('Job sent to farm : {}#jid={}'.format(TRACTOR_URL, jobId))


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


def run():
    """HDA 'Send To Farm' button callback script"""
    if checkUnsavedChanges():
        return

    addToPathEnvVar()
    job = HtoTJob()
    job.sendToFarm()


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

    if outputDriverType not in ['ifd', 'ris']:
        return

    node.parm('rangex').setExpression('ch("{}/f1")'.format(outputDriverPath))
    node.parm('rangey').setExpression('ch("{}/f2")'.format(outputDriverPath))
