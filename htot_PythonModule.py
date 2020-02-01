#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module: htot.htot_PythonModule
:platform: Windows
:version: v2.1.0
:description: Core functions for HDA module that allows spooling jobs to Tractor
    This file is just a copy of what's inside the HDA "Script" tab
:author: Valentin David <vdavid.pro@gmail.com>
:license: MIT License
"""
# --------------------------------------------------------------------------------------------------
# Python built-in modules import
# --------------------------------------------------------------------------------------------------
import os
import random
import string
import subprocess
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
RENDERER_MAPPING = {
    'ifd': {'niceName': 'Mantra', 'archiveExt': 'ifd'},
    'ris': {'niceName': 'Renderman', 'archiveExt': 'rib'},  # TODO : remove before merge as this is not supported
    'ris::22': {'niceName': 'Renderman', 'archiveExt': 'rib'},
    'arnold': {'niceName': 'Arnold', 'archiveExt': 'ass'},
}


# --------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------


class HtoTJob(object):
    """Defines a Houdini to Tractor job"""

    def __init__(self):
        """Evaluate HtoT node parameters to get job arguments"""
        self.sceneFile = hou.hipFile.path()
        self.node = hou.pwd()

        outputDriverRelativePath = self.node.evalParm('outputDriver')

        # We need to raise an error if the output driver does not exist or is not of the right type
        if hou.node(outputDriverRelativePath) is None:
            text = 'Node does not exist : "{}"'.format(outputDriverRelativePath)
            raise RuntimeError(text)

        self.outputDriver = hou.node(outputDriverRelativePath)
        self.outputDriverPath = self.outputDriver.path()
        self.outputDriverType = hou.node(self.outputDriverPath).type().name()

        if self.outputDriverType not in RENDERER_MAPPING.keys():
            text = 'Node "{}" is of type "{}". Correct types are {}'.format(
                self.outputDriverPath,
                self.outputDriverType,
                RENDERER_MAPPING.keys()
            )
            raise TypeError(text)

        # Prepare temp scene file
        self.sceneDir = os.path.dirname(self.sceneFile)
        ext = self.sceneFile.split('.')[-1]
        self.randomStr = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(6)])
        self.tempSceneFileName = 'htot_{}.{}'.format(self.randomStr, ext)
        self.tempSceneFile = os.path.join(self.sceneDir, self.tempSceneFileName)

        # Job Options tab
        # Tractor Job Attributes
        self.renderer = self.node.evalParm('renderer')
        self.archiveExt = RENDERER_MAPPING.get(self.outputDriverType).get('archiveExt')
        self.start = self.node.evalParm('rangex') or hou.expandString('$FSTART')
        self.end = self.node.evalParm('rangey') or hou.expandString('$FEND')
        self.sceneFileName = hou.expandString('$HIPNAME')

        defaultTitle = '[{}][{}] Render frames {} - {}'.format(
            self.sceneFileName,
            self.renderer,
            self.start,
            self.end
        )
        self.jobTitle = self.node.evalParm('title') or defaultTitle
        self.paused = self.node.evalParm('paused_tgl')
        projects = self.node.evalParm('projects') or ''
        self.projects = projects.replace(' ', '').split(',')
        self.priority = self.node.evalParm('priority')
        self.maxActiveTgl = self.node.evalParm('maxActive_tgl')
        self.maxActive = self.node.evalParm('maxActive')
        self.comment = self.node.evalParm('comment')

        # Archives
        self.archivesGeneration = self.node.parm('archivesGeneration').evalAsString()
        self.archivesGenCmds = [] if self.archivesGeneration == 'local' else None
        self.binaryArchives = self.node.evalParm('binaryArchives_tgl')

        # Advanced tab
        self.houdiniBinPath = self.node.evalParm('houdiniBinPath') or hou.expandString('$HFS/bin')
        self.htotTempDir = self.node.evalParm('tempDir') or hou.expandString('$HIP/htot')
        self.deleteTempScene = self.node.evalParm('deleteTempScene_tgl')
        self.service = self.node.evalParm('service') or 'PixarRender'
        self.tractorUrl = self.node.evalParm('tractorUrl')
        self.debugMode = self.node.evalParm('debugMode_tgl')

        # Deduce other data
        self.archiveOutput = os.path.join(self.htotTempDir, 'htot_{}.$F4.{}'.format(self.randomStr, self.archiveExt))

        # cast to needed types
        self.start = int(self.start)
        self.end = int(self.end)
        self.priority = int(self.priority)

        # normalize paths to forward slashes
        self.houdiniBinPath = self.houdiniBinPath.replace('\\', '/')
        self.archiveOutput = self.archiveOutput.replace('\\', '/')
        self.tempSceneFile = self.tempSceneFile.replace('\\', '/')

        self.toDelete = [self.tempSceneFile] if self.deleteTempScene else []

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
        job.serialsubtasks = True

        masterTask = author.Task()
        masterTask.title = 'Render all'
        job.addChild(masterTask)

        # Create one task per frame
        for frame in range(self.start, self.end + 1):

            if self.archivesGeneration:
                # Generate archive
                archiveTask = author.Task()
                archiveTask.title = 'Generate {} for frame {}'.format(self.archiveExt, frame)
                archiveTask.service = self.service
                archiveFile = self.archiveOutput.replace('$F4', str(frame).zfill(4))
                archiveTaskCmd = author.Command()
                archiveTaskCmd.argv = [os.path.join(self.houdiniBinPath, 'hbatch.exe').replace('\\', '/')]
                archiveTaskCmd.argv.append('-c')
                hscriptCmd = 'render -V -f {} {} {}; quit'.format(frame, frame, self.outputDriverPath)
                archiveTaskCmd.argv.append(hscriptCmd)
                archiveTaskCmd.argv.append('-w')  # WATCHME : suppress load warnings
                archiveTaskCmd.argv.append('-i')  # WATCHME : simplified
                archiveTaskCmd.argv.append('-V')  # WATCHME : verbosity to know what exit codes should retry
                archiveTaskCmd.argv.append('9')  # TODO : change to 1 before merge
                archiveTaskCmd.argv.append(self.tempSceneFile)
                # archiveTaskCmd.retryrc = [1, 2, 3, 4, 5]  # WATCHME : exit codes that will restart the task
                archiveTask.addCommand(archiveTaskCmd)

                # Add archive file to be deleted by cleanup task
                self.toDelete.append(archiveFile)

                # Render generated archive
                renderTask = author.Task()
                renderTask.title = 'Render frame {}'.format(frame)
                renderTask.service = self.service
                renderTaskCmd = author.Command()

                # Renderman
                if self.renderer == 'Renderman':
                    renderTaskCmd.argv = ['prman.exe', archiveFile]

                # Mantra
                elif self.renderer == 'Mantra':
                    renderTaskCmd.argv = [os.path.join(self.houdiniBinPath, 'mantra.exe').replace('\\', '/')]
                    renderTaskCmd.argv.extend(['-f', archiveFile])
                    renderTaskCmd.retryrc = [1, 2, 3, 4, 5]  # WATCHME : exit codes

                # Arnold  # TODO
                elif self.renderer == 'Arnold':
                    raise NotImplementedError()

                renderTask.addCommand(renderTaskCmd)

                if self.archivesGeneration == 'remote':
                    renderTask.addChild(archiveTask)

                elif self.archivesGeneration == 'local':
                    self.archivesGenCmds.append(archiveTaskCmd.argv)

            else:
                # Render without generating an archive
                renderTask = author.Task()
                renderTask.title = 'Render frame {}'.format(frame)
                renderTask.service = self.service
                renderTaskCmd = author.Command()
                renderTaskCmd.argv = [os.path.join(self.houdiniBinPath, 'hbatch.exe').replace('\\', '/')]
                renderTaskCmd.argv.append('-c')
                hscriptCmd = 'render -V -f {} {} {}; quit'.format(frame, frame, self.outputDriverPath)
                renderTaskCmd.argv.append(hscriptCmd)
                renderTaskCmd.argv.append('-w')  # suppress load warnings
                renderTaskCmd.argv.append(self.tempSceneFile)
                renderTaskCmd.argv.append('-w')  # WATCHME : suppress load warnings
                renderTaskCmd.argv.append('-i')  # WATCHME : simplified
                renderTaskCmd.argv.append('-V')  # WATCHME : verbosity to know what exit codes should retry
                renderTaskCmd.argv.append('9')  # TODO : change to 1 before merge
                renderTaskCmd.retryrc = [1, 2, 3, 4, 5]  # WATCHME : exit codes
                renderTask.addCommand(renderTaskCmd)

            masterTask.addChild(renderTask)

        # Cleanup
        cleanupCmd = author.Command()
        cleanupCmd.argv = ['TractorBuiltIn', 'File', 'delete']
        cleanupCmd.argv.extend(self.toDelete)
        job.addCleanup(cleanupCmd)

        return job

    def sendToFarm(self):
        """Send job to farm"""

        if self.debugMode:
            log.info('DEBUG MODE IS ON')
            log.info('Job to send : \n\n')
            print self.job.asTcl()
            return

        # Generate archives local
        if self.archivesGeneration == 'local' and self.archivesGenCmds is not None:

            title = 'Generating {} archives'.format(self.archiveExt.title())
            with hou.InterruptableOperation(title, open_interrupt_dialog=True) as progress:
                processCount = len(self.archivesGenCmds)
                count = 1

                for process in self.archivesGenCmds:
                    sui = subprocess.STARTUPINFO()
                    sui.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.call(process, startupinfo=sui)
                    percent = float(count) / float(processCount)
                    progress.updateProgress(percent)
                    count += 1

        jobId = self.job.spool()

        if jobId:
            hou.ui.displayMessage(text='Job sent to Tractor : \n{}#jid={}'.format(self.tractorUrl, jobId))

    def prepareTempScene(self):
        """This will save a temporary scene to be used by Tractor blades

        This scene is a copy of the original scene with some alterations
        to make it render archives instead of images directly
        """
        if self.debugMode:
            return

        createPaths(self.htotTempDir)

        # Mantra  # WATCHME
        if self.renderer == 'Mantra':
            self.outputDriver.parm('soho_outputmode').set(True)
            self.outputDriver.parm('soho_diskfile').set(self.archiveOutput)
            self.outputDriver.parm('vm_inlinestorage').set(True)
            self.outputDriver.parm('vm_binarygeometry').set(self.binaryArchives)
            # ifdsDir = os.path.join(self.htotTempDir, 'ifds', 'storage')
            # hou.parm('{}/vm_tmpsharedstorage'.format(self.outputDriverPath)).set(ifdsDir)

            hou.hipFile.save(self.tempSceneFile)

            self.outputDriver.parm('soho_outputmode').set(False)
            hou.hipFile.save(self.sceneFile)

        # Renderman
        elif self.renderer == 'Renderman':
            self.outputDriver.parm('ri_makedir_0').set(True)
            self.outputDriver.parm('ri_device_0').set('openexr')
            correctOutputName = self.outputDriver.evalParm('ri_display_0')

            # TODO : theres a fuckup here where the first frame gets overwritten by every task
            print 'correctOutputName', correctOutputName
            correctOutputName = correctOutputName.replace('$HIPNAME', self.sceneFileName)
            print 'correctOutputName', correctOutputName
            # correctOutputName.replace('$F4')
            self.outputDriver.parm('ri_display_0').set(correctOutputName)

            self.outputDriver.parm('diskfile').set(bool(self.archivesGeneration))
            self.outputDriver.parm('binaryrib').set(self.binaryArchives)
            self.outputDriver.parm('soho_diskfile').set(self.archiveOutput)

            hou.hipFile.save(self.tempSceneFile)

            self.outputDriver.parm('diskfile').set(False)
            hou.hipFile.save(self.sceneFile)

        # Arnold  # WATCHME
        elif self.renderer == 'Arnold':
            self.outputDriver.parm('ar_ass_export_enable').set(True)
            self.outputDriver.parm('ar_ass_file').set(self.archiveOutput)
            self.outputDriver.parm('ar_binary_ass').set(self.binaryArchives)

            hou.hipFile.save(self.tempSceneFile)

            self.outputDriver.parm('ar_ass_export_enable').set(False)
            hou.hipFile.save(self.sceneFile)


def checkUnsavedChanges():
    """This will check if the current scene has unsaved changes"""
    if hou.hipFile.hasUnsavedChanges():
        text = 'Current scene has unsaved changes. Please save your scene and retry'
        hou.ui.displayMessage(text=text, severity=hou.severityType.Warning)
        return True

    else:
        return False


def createPaths(paths):
    """This will create the needed paths if they don't exist

    :param paths: The paths to create
    :type paths: str | list of str
    """
    if isinstance(paths, basestring):
        paths = [paths]

    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)


def run():
    """HDA 'Spool To Tractor' button callback script"""
    if checkUnsavedChanges():
        return

    job = HtoTJob()
    job.prepareTempScene()
    job.sendToFarm()


def onOutputDriverParmChange():
    """Callback script executed every time the 'outputDriver' parameter is changed

    If the outputDriver is a supported render node, this will link some parameters
    """
    node = hou.pwd()
    outputDriverPath = node.evalParm('outputDriver')
    outputDriver = hou.node(outputDriverPath)

    # We need to return early to avoid slowing down Houdini too much
    if outputDriver is None:
        return

    outputDriverType = outputDriver.type().name()

    if outputDriverType not in RENDERER_MAPPING.keys():
        return

    renderer = RENDERER_MAPPING.get(outputDriverType).get('niceName')

    node.parm('rangex').setExpression('ch("{}/f1")'.format(outputDriverPath))
    node.parm('rangey').setExpression('ch("{}/f2")'.format(outputDriverPath))
    node.parm('renderer').set(renderer)
