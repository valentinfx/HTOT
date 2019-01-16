# HTOT

# Shell command in Houdini :
# hython htot.py $HIPFILE `chs("../outputDriver")` `chs("../f1")` `chs("../f2")` `chs("../jobPriority")`

import os, sys,subprocess, datetime
from shutil import copyfile
import hou

# Get params from shell command
sceneFile = sys.argv[1]
renderNode = sys.argv[2]
startFrame = sys.argv[3]
endFrame = sys.argv[4]
jobPriority = sys.argv[5]

# Check and create directories
htotPath = os.path.split(sceneFile)[0]+'/htot'
renderPath = os.path.split(sceneFile)[0]+'/render'
ifdsPath = os.path.split(sceneFile)[0]+'/ifds'

checkPaths = [htotPath,renderPath,ifdsPath]
for i in checkPaths:
	if not os.path.exists(i):
		os.makedirs(i)

# Create timestamp to name temp scene file
ts = datetime.datetime.now()
timeStamp = '%s%s%s%s%s%s'%(ts.year,ts.month,ts.day,ts.hour,ts.minute,ts.second)
# Create temp scene file path with forward slashes
tempSceneFile = os.path.join(os.path.split(sceneFile)[0],timeStamp + '_' + os.path.split(sceneFile)[1]).replace(os.sep, '/')

# Create some variables that will be used for .alf file authoring
sceneName = os.path.splitext(os.path.split(sceneFile)[1])[0]
renderNodeSimplified = (os.path.split(renderNode)[1])
jobTitle = sceneName+'_'+renderNodeSimplified+'_'+startFrame+'-'+endFrame

# Load Houdini scene
hou.hipFile.load(sceneFile,suppress_save_prompt=True)

# Set Output Driver to render IFD files
hou.parm("%s/soho_outputmode"%renderNode).set(1)
hou.parm('%s/soho_diskfile'%renderNode).set('$HIP/ifds/$OS.$F.ifd')
# Get 'Output Picture' parameter string
vm_pictureStr = hou.parm('%s/vm_picture'%renderNode).unexpandedString()
# Replace $HIPNAME by the original scene name
if '$HIPNAME' in vm_pictureStr:
	vm_pictureStr = vm_pictureStr.replace('$HIPNAME',sceneName)
	hou.parm('%s/vm_picture'%renderNode).set(vm_pictureStr)
print('Output pictures will be saved to : %s'%vm_pictureStr)

# Save temp Houdini scene
# This scene will be used for render
hou.hipFile.save(file_name=tempSceneFile,save_to_recent_files=True)
print("Scene copied to : "+ tempSceneFile)

# Create .alf file path with forward slashes
alfFile = os.path.join(htotPath,jobTitle+'.alf').replace(os.sep, '/')

# Check if .alf file already exists and delete
if os.path.isfile(alfFile):
	os.remove(alfFile)


# .alf file authoring
f = open(alfFile,'w+')

# First line : set job title, priority, service and cleanup
f.write('Job -title {%s} -priority {%s} -service { PixarRender } -cleanup {\n'%( jobTitle, jobPriority ) )
# Write cleanup tasks, executed after every other tasks
f.write('	RemoteCmd { {TractorBuiltIn} {File} {delete} {%D(' + tempSceneFile + ')} }\n' )
f.write('	RemoteCmd { {TractorBuiltIn} {File} {delete} {%D(' + alfFile + ')} }\n' )
f.write('	RemoteCmd { {TractorBuiltIn} {File} {delete} {%D(' + ifdsPath + ')} }\n' )
# Write a master task
f.write('	} -serialsubtasks 1 -subtasks {\n')
f.write('		Task {Render} -serialsubtasks 0\n' )
# Write IFD task
f.write('		Task {IFD} -serialsubtasks 1 -cmds {\n' )
f.write('			RemoteCmd { "hbatch.exe" -c "render -V -f ' + startFrame + ' ' + endFrame + ' ' + renderNode + '; quit" ' + tempSceneFile + ' } -service { PixarRender }\n')
f.write('			}\n' )
# Write master track for render with Mantra
f.write('		Task {Render Frames} -serialsubtasks 0 -subtasks {\n')
f.write('			Task {Render frames %s to %s} -serialsubtasks 0 -subtasks {\n'%( startFrame, endFrame) )
# Write one task for each frame to render with Mantra
for i in range(int(startFrame), int(endFrame)+1):
	f.write('				Task {Render frame %d} -cmds {\n'%i )
	f.write('					RemoteCmd { "mantra.exe" -V 5 -f "%s/%s.%s.ifd" } -service { PixarRender }\n'%(ifdsPath,renderNodeSimplified,i))
	f.write('				}\n')
# Close last braces
f.write('			}\n')
f.write('		}\n')
f.write('	}\n')
# Close file
f.close()

print("Job script file saved to : " + alfFile)

# Send .alf file to tractor
print("Spooling job to Tractor...")
subprocess.call("C:/PROGRA~1/Pixar/Tractor-2.2/bin/tractor-spool.bat " + alfFile )

os.system('pause')