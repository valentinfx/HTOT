#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:module: htot.htot_PythonModule
:platform: Windows
:version: v2.1.1
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
log.basicConfig(level='INFO')

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
        self.snapshotSceneFileName = 'htot_{}.{}'.format(self.randomStr, ext)
        self.snapshotScene = os.path.join(self.sceneDir, self.snapshotSceneFileName)

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

        # Cast to needed types
        self.start = int(self.start)
        self.end = int(self.end)
        self.priority = int(self.priority)

        # normalize paths to forward slashes
        self.houdiniBinPath = self.houdiniBinPath.replace('\\', '/')
        self.archiveOutput = self.archiveOutput.replace('\\', '/')
        self.snapshotScene = self.snapshotScene.replace('\\', '/')

        self.toDelete = [self.snapshotScene] if self.deleteTempScene else []

        self.job = self.createJob()

    def prepareSnapshotScene(self):
        """This will save a temporary snapshot scene to be used by Tractor blades

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

            hou.hipFile.save(self.snapshotScene, save_to_recent_files=False)

            self.outputDriver.parm('soho_outputmode').set(False)
            hou.hipFile.save(self.sceneFile)

        # Renderman
        elif self.renderer == 'Renderman':
            self.outputDriver.parm('ri_makedir_0').set(True)
            self.outputDriver.parm('ri_device_0').set('openexr')
            originalOutputName = self.outputDriver.parm('ri_display_0').unexpandedString()
            correctOutputName = originalOutputName.replace('$HIPNAME', self.sceneFileName)
            self.outputDriver.parm('ri_display_0').set(correctOutputName)

            self.outputDriver.parm('diskfile').set(bool(self.archivesGeneration))
            self.outputDriver.parm('binaryrib').set(self.binaryArchives)
            self.outputDriver.parm('soho_diskfile').set(self.archiveOutput)

            hou.hipFile.save(self.snapshotScene, save_to_recent_files=False)

            self.outputDriver.parm('ri_display_0').set(originalOutputName)
            self.outputDriver.parm('diskfile').set(False)
            hou.hipFile.save(self.sceneFile)

        # Arnold  # WATCHME
        elif self.renderer == 'Arnold':
            self.outputDriver.parm('ar_ass_export_enable').set(True)
            self.outputDriver.parm('ar_ass_file').set(self.archiveOutput)
            self.outputDriver.parm('ar_binary_ass').set(self.binaryArchives)

            hou.hipFile.save(self.snapshotScene, save_to_recent_files=False)

            self.outputDriver.parm('ar_ass_export_enable').set(False)
            hou.hipFile.save(self.sceneFile)

    def createArchiveGenTask(self):
        """Create a unique task that will render all frames in ifd/ass/rib

        :return: The archives generation task
        :rtype: :class:`author.Task`
        """
        archiveTask = author.Task()
        archiveTask.title = 'Generate {} files'.format(self.archiveExt)
        archiveTask.service = self.service

        archiveTaskCmd = author.Command()
        archiveTaskCmd.argv = [os.path.join(self.houdiniBinPath, 'hbatch.exe').replace('\\', '/')]
        archiveTaskCmd.argv.append('-c')
        # hscriptCmd = 'tcur {}; render -w -i -V 1 -f {} {} {}; quit'.format(
        hscriptCmd = 'render -w -i -V 2 -f {} {} {}; quit'.format(
            self.start,
            self.end,
            self.outputDriverPath
        )
        archiveTaskCmd.argv.append(hscriptCmd)
        archiveTaskCmd.argv.append(self.snapshotScene)
        archiveTaskCmd.retryrc = range(0, 11)  # WATCHME : exit codes that will restart the task
        archiveTask.addCommand(archiveTaskCmd)

        # Add archive files to be deleted by cleanup task
        archiveFiles = [
            self.archiveOutput.replace('$F4', str(frame).zfill(4))
            for frame in range(self.start, self.end + 1)
        ]

        self.toDelete.extend(archiveFiles)

        return archiveTask

    def createRenderArchiveTasks(self):
        """Create one task per frame that will render ifd/ass/rib files to a picture

        :return: A set of tasks to render archives
        :rtype: list of :class:`author.Task`
        """
        renderTasks = []
        for frame in range(self.start, self.end + 1):

            archiveFile = self.archiveOutput.replace('$F4', str(frame).zfill(4))

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
                renderTaskCmd.retryrc = range(0, 11)  # WATCHME : exit codes

            # Arnold  # SOMEDAY
            elif self.renderer == 'Arnold':
                raise NotImplementedError()

            renderTask.addCommand(renderTaskCmd)

            renderTasks.append(renderTask)

        return renderTasks

    def createRenderTasks(self):
        """Create one task per frame that will render a picture directly

        :return: A set of tasks to render pictures
        :rtype: list of :class:`author.Task`
        """
        renderTasks = []
        for frame in range(self.start, self.end + 1):
            renderTask = author.Task()
            renderTask.title = 'Render frame {}'.format(frame)
            renderTask.service = self.service
            renderTaskCmd = author.Command()
            renderTaskCmd.argv = [os.path.join(self.houdiniBinPath, 'hbatch.exe').replace('\\', '/')]
            renderTaskCmd.argv.append('-c')
            hscriptCmd = 'tcur {}; render -w -i -V -f {} {} {}; quit'.format(
                frame,
                frame,
                frame,
                self.outputDriverPath
            )
            renderTaskCmd.argv.append(hscriptCmd)
            renderTaskCmd.argv.append(self.snapshotScene)
            # renderTaskCmd.argv.append('-w')  # WATCHME : suppress load warnings
            # renderTaskCmd.argv.append('-i')  # WATCHME : simplified
            renderTaskCmd.retryrc = range(0, 11)  # WATCHME : exit codes
            renderTask.addCommand(renderTaskCmd)

        return renderTasks

    def createJob(self):
        """Create a Houdini tractor job from htot node parameters

        :return: The complete job to send to tractor
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

        # Create master task
        masterTask = author.Task()
        masterTask.title = 'Master Task'
        masterTask.serialsubtasks = True
        job.addChild(masterTask)

        # Create a master render task
        masterRenderTask = author.Task()
        masterRenderTask.title = 'Render all frames'

        if self.renderer == 'Renderman':
            try:
                import prman
                rmVersion = prman.Version.replace('RenderManProServer', 'rfm')  # WATCHME
                job.envkey = [rmVersion]

            except ImportError:
                pass

        if self.archivesGeneration:
            if self.archivesGeneration == 'remote':
                masterArchivesTask = author.Task()
                masterArchivesTask.title = 'Generate all archives'
                masterArchivesTask.addChild(self.createArchiveGenTask())
                masterTask.addChild(masterArchivesTask)

            elif self.archivesGeneration == 'local':
                self.createArchiveGenTask()

            for task in self.createRenderArchiveTasks():
                masterRenderTask.addChild(task)

        else:
            for task in self.createRenderTasks():
                masterRenderTask.addChild(task)

        masterTask.addChild(masterRenderTask)

        # Cleanup
        cleanupCmd = author.Command()
        cleanupCmd.argv = ['TractorBuiltIn', 'File', 'delete']
        cleanupCmd.argv.extend(self.toDelete)
        job.addCleanup(cleanupCmd)

        return job

    def sendToFarm(self):
        """Send job to farm"""

        if self.debugMode:
            log.info('Debug mode is on')
            log.info('Job to send : \n\n')
            print self.job.asTcl()
            return

        # Generate archives local
        if self.archivesGeneration == 'local':
            self.generateArchivesLocaly()

        jobId = self.job.spool()

        if jobId:
            hou.ui.displayMessage(text='Job sent to Tractor : \n{}#jid={}'.format(self.tractorUrl, jobId))

    def generateArchivesLocaly(self):
        """This will execute an inline Hscript to generate the archives"""
        cmd = 'render -w -i -V 1 -f {} {} {}'.format(self.start, self.end, self.outputDriverPath)

        # Mantra  # WATCHME
        if self.renderer == 'Mantra':
            self.outputDriver.parm('soho_outputmode').set(True)
            hou.hscript(cmd)
            self.outputDriver.parm('soho_outputmode').set(False)

        # Renderman
        elif self.renderer == 'Renderman':
            self.outputDriver.parm('diskfile').set(True)
            hou.hscript(cmd)
            self.outputDriver.parm('diskfile').set(False)

        # Arnold
        elif self.renderer == 'Arnold':
            self.outputDriver.parm('ar_ass_export_enable').set(True)
            hou.hscript(cmd)
            self.outputDriver.parm('ar_ass_export_enable').set(False)


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
    """HDA 'Spool To Tractor' button callback script

    This is the main function of the node
    """
    if checkUnsavedChanges():
        return

    job = HtoTJob()
    job.prepareSnapshotScene()
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
        log.warning(
            'Output Driver \'{}\' of type \'{}\' is not supported by HtoT'.format(
                outputDriver.name(),
                outputDriverType
            )
        )
        return

    renderer = RENDERER_MAPPING.get(outputDriverType).get('niceName')

    node.parm('rangex').setExpression('ch("{}/f1")'.format(outputDriverPath))
    node.parm('rangey').setExpression('ch("{}/f2")'.format(outputDriverPath))
    node.parm('renderer').set(renderer)
    node.parm('outputDriver').set(outputDriver.path())
