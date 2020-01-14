# HtoT v2.0.0
### Houdini To Tractor

HtoT is intended to work with Tractor 2.3, Houdini 17 and up. 
It currently supports sending jobs for both Renderman and Mantra.

##### How set up your machines
These steps should be done by your system administrator (or IT team)
1. Make sure Houdini 17+ and Tractor 2.3 are both correctly installed on every machine
2. Add Tractor's Python API path to every machine's PYTHONPATH environment variable. The path should look like :
`C:/Program Files/Pixar/Tractor-2.3/lib/python2.7/Lib/site-packages`

##### How to 'install' HtoT
1. Copy **htot.hdanc** to your Houdini asset library. Ideally this should be a shared directory for every machine.
For more details, check out : 
[sidefx.com/docs/houdini/assets/install](http://www.sidefx.com/docs/houdini/assets/install.html)
2. Since version 2, you do not need to copy the python files anywhere, they are just a copy of the contents found in the
HDA's **Scripts** tab

##### How to use HtoT
1. Create a `htot` node in a `/out` context
2. Specify the Output Driver (e.g. `/out/mantra1` or `/out/RIS1`). This is the only mandatory field before you can
spool a job to Tractor.
3. Set your job parameters :
   - Frame range : start and end frame (default : `$FSTART`,  `$FEND`)
   - Title : will be used to set the job title (default : `$HIPNAME`)
   - Projects : name of the projects attached to this job, separated by commas
   - Priority : priority of the job (default : `1`)
   - Max Active : cap the number of simultaneously active tasks from that job (default : `0`)
   - Debug Mode : debug mode will only print your job to the command output instead of spooling it (default : `False`)
4. You  may want to edit the default Houdini's bin path in the "Advanced" tab. 
5. You can also change Tractor's url in case the default doesn't work for you

#### Known limitations
