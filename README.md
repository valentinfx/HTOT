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
 
1. Specify the Output Driver (e.g. `/out/mantra1` or `/out/RIS1`). This is the only mandatory field before you can
spool a job to Tractor.
2. Set your job parameters :
- Frame range (defaults : `$FSTART`,  `$FEND`)
- Shot Name (this will be used to set the job title) (default : `$HIPNAME`)
- Project Name

#### Known limitations
- At the moment, it is not possible to use HTOT if your scene uses ```$HIPNAME``` (e.g. in filecache nodes). You have to manually replace them with your scene name (except for Mantra nodes).
- The post-job cleanup won't delete ```$HIP/ifds/storage```. You will have to manually remove it after all your jobs are finished.
