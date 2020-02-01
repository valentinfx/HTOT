# HtoT v2.0.0
## Houdini To Tractor

HtoT is intended to work with Tractor 2.3, Houdini 17 and up.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)


## Getting Started
### How to set up your machines
These steps should be done by your system administrator (or IT team)
1. Make sure Houdini 17+ and Tractor 2.3 are both correctly installed on every machine
2. On every machine that needs to send Tractor jobs, add Tractor's Python API path to every 
machine's **PYTHONPATH** environment variable. The path should look like :
`C:/Program Files/Pixar/Tractor-2.3/lib/python2.7/Lib/site-packages`

### How to 'install' HtoT
1. Copy **htot.hdanc** to your Houdini asset library. Ideally this should be a shared directory for every machine.
For more details, check out : 
[sidefx.com/docs/houdini/assets/install](http://www.sidefx.com/docs/houdini/assets/install.html)
2. Since version 2, you do not need to copy the python files anywhere, they are just a copy of the contents found
in the HDA's **Scripts** tab

### How to use HtoT
1. Create a `htot` node in a `/out` context
2. Specify the Output Driver (e.g. `/out/mantra1` or `/out/RIS1`). This is the only mandatory field before you can
spool a job to Tractor.
3. Set your job parameters :
   - Frame range : start and end frame (default : `$FSTART`,  `$FEND`)
   - Title : title of your tractor job (default : `[$HIPNAME][<renderer>] Render frames <start> - <end>`)
   - Start Paused : if enabled, the job will be spool and immediately paused (default : disabled)
   - Projects : name of the projects attached to this job, separated by commas
   - Priority : priority of the job (default : `1`)
   - Max Active : cap the number of simultaneously active tasks from that job (default : disabled)
   - Debug Mode : debug mode will only print your job to the command output instead of spooling it (default : `False`)
4. Hit 'Spool To Tractor' !
5. For more information, you can click the Help button on HtoT's parameters interface

## Features

- Spool Mantra and Renderman jobs
- Generate ifd/rib archives locally or as part of Tractor job

## Known limitations

- Arnold is already partially implemented although it won't go further as I have no way to test
- No support for other renderers
- At the moment archives are generated then frames are rendered from these archives. This is to avoid using
one Houdini license AND one render engine license per blade for the entire duration of the render. In the future 
it would be interesting to be able to choose (for cases where licenses are not a problem and/or archives will
take too much space).

## Contribute

You're welcome to contribute to this project by creating a branch and issuing a merge request. I've made it so
implementing a new render engine should be easy.