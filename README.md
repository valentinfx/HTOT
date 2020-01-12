# HtoT v2.0.0
### Houdini To Tractor

HtoT is intended to work with Tractor 2.3, Houdini 17 and up, Mantra and Renderman 23.

##### How set up your machines
These steps should be done by your system administrator
1. Make sure Houdini 17 and Tractor 2.3 are correctly installed on every machine
2. Add Houdini bin and Tractor path to every machine's PATH environment variable. These paths should look like :
`C:\Program Files\Side Effects Software\Houdini 17.0.352\bin` and `C:/Program Files/Pixar/Tractor-2.3`

##### How to 'install' HtoT
1. Copy ```htot.hdanc``` to your Houdini asset library. Ideally this should be a shared directory for every machine.
For more details, check out : [sidefx.com/docs/houdini/assets/install](http://www.sidefx.com/docs/houdini/assets/install.html)
2. Since version 2, you do not need to copy `htot.py` anywhere, this file is just a copy of the contents found in the
HDA's Script tab

##### How to use HTOT
 
1. Create a `htot` node in a `/OUT` context
2. Specify the Output Driver (e.g. `/out/mantra1` or `/out/RIS1`). This is the only mandatory field before you can
spool a job to Tractor.
3. Set your job parameters :
   - Frame range : start and end frame (default : `$FSTART`,  `$FEND`)
   - Shot Name : will be used to set the job title (default : `$HIPNAME`)
   - Projects Name : Name of the projects attached to this job, separated by commas
   - Priority : priority of the job (default : `1`)
   - Max Active : cap the number of simultaneously active tasks from that job (default : `0`)
   - Debug Mode : debug mode will only print your job to the command output instead of spooling it (default : `False`)
4. You  may want to edit the default Tractor Api path and Houdini path in the "Advanced" tab. Note that this will not
change the paths for the blades but only for the current machine
4. You can also change Tractor's url in case the default doesn't work for you

#### Known limitations
