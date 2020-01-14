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
TRACTOR_URL = 'http://tractor-engine/tv/'  # TODO : use tractor URL API instead
# TEMP_DIR = NODE.evalParm('tempDir') or hou.expandString('$HIP/rfhTemp')
NODE_TYPES_MAPPING = {
    'ifd': 'Mantra',
    'ris': 'RfH',
    'ris::22': 'RfH 22',
    'ris::23': 'RfH 23'
}

# --------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------


# TODO : hda Help tab


class HtoTJob(object):
    """Defines a Houdini to Tractor job"""

    def __init__(self):
        """Evaluate HtoT node parameters to get job arguments"""
        self.sceneFile = hou.hipFile.path()
        self.node = hou.pwd()

        outputDriver = self.node.evalParm('outputDriver')

        # We need to raise an error if the output driver does not exist or is not of the right type
        if hou.node(outputDriver) is None:
            text = 'Node does not exist : "{}"'.format(outputDriver)
            raise RuntimeError(text)

        self.outputDriver = hou.node(outputDriver).path()
        self.outputDriverType = hou.node(self.outputDriver).type().name()

        if self.outputDriverType not in NODE_TYPES_MAPPING:
            text = 'Node "{}" is of type "{}". Correct types are {}'.format(
                self.outputDriver,
                self.outputDriverType,
                NODE_TYPES_MAPPING.keys()
            )
            raise TypeError(text)

        self.renderer = self.node.evalParm('renderer')
        self.start = self.node.evalParm('rangex') or hou.expandString('$FSTART')
        self.end = self.node.evalParm('rangey') or hou.expandString('$FEND')

        # Evaluate first tab parameters values
        defaultTitle = '[{}][{}] Render frames {} - {}'.format(
            hou.expandString('$HIPNAME'),
            self.renderer,
            self.start,
            self.end
        )
        self.jobTitle = self.node.evalParm('title') or defaultTitle
        self.paused = self.node.evalParm('paused')
        projects = self.node.evalParm('projects') or ''
        self.projects = projects.replace(' ', '').split(',')
        self.priority = self.node.evalParm('priority')
        self.maxActiveTgl = self.node.evalParm('maxActive_tgl')
        self.maxActive = self.node.evalParm('maxActive')
        self.comment = self.node.evalParm('comment')

        # Evaluate "Advanced" tab parameters values
        self.houdiniBinPath = self.node.evalParm('houdiniBinPath') or hou.expandString('$HFS/bin')
        self.service = self.node.evalParm('service') or 'PixarRender'
        self.tractorUrl = self.node.evalParm('tractorUrl') or TRACTOR_URL
        self.debugMode = self.node.evalParm('debugMode')

        # cast to needed types
        self.start = int(self.start)
        self.end = int(self.end)
        self.priority = int(self.priority)

        self.job = self.createJob()

    def createJob(self):
        """Create Houdini tractor job from parameters

        :return: A Tractor Job object
        :rtype: :class:`author.Job`
        """
        # Create job
        job = author.Job()
        job.title = self.jobTitle
        if self.paused:
            job.paused = True
        job.projects = self.projects
        job.priority = self.priority
        if self.maxActiveTgl:
            job.maxactive = self.maxActive
        job.comment = self.comment
        job.service = self.service

        # Create one task per frame
        for frame in range(self.start, self.end + 1):
            renderTask = author.Task()
            renderTask.title = 'Render frame {}'.format(frame)

            cmd = author.Command()
            hbatchPath = os.path.join(self.houdiniBinPath, 'hbatch.exe')
            cmd.argv = [
                '"{}" -c "render -V -f {} {} {} ; quit" {}'.format(
                    hbatchPath,
                    frame,
                    frame,
                    self.outputDriver,
                    self.sceneFile
                )
            ]
            renderTask.addCommand(cmd)

            job.addChild(renderTask)

        return job

    def sendToFarm(self):
        """Send job to farm"""
        if self.debugMode:
            log.info('DEBUG MODE IS ON')
            log.info('Job to send : \n')
            print self.job.asTcl()
        else:
            jobId = self.job.spool()
            if jobId:
                print 'Job sent to Tractor : {}#jid={}'.format(TRACTOR_URL, jobId)


def checkUnsavedChanges():
    """This will check if the current scene has unsaved changes"""
    if hou.hipFile.hasUnsavedChanges():
        text = 'Current scene has unsaved changes. Please save your scene and retry'
        hou.ui.displayMessage(text, severity=hou.severityType.Warning)
        return True

    else:
        return False


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
    """HDA 'Spool To Tractor' button callback script"""
    if checkUnsavedChanges():
        return

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

    if outputDriverType not in NODE_TYPES_MAPPING.keys():
        return

    renderer = NODE_TYPES_MAPPING.get(outputDriverType)

    node.parm('rangex').setExpression('ch("{}/f1")'.format(outputDriverPath))
    node.parm('rangey').setExpression('ch("{}/f2")'.format(outputDriverPath))
    node.parm('renderer').set(renderer)
