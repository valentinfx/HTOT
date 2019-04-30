# Houdini To Tractor

HTOT is intended to work with Tractor 2.2, Houdini 17 and Mantra.

##### How set up your machines
These steps should be done by your system administrator
1. Make sure Houdini 17 and Tractor 2.2 are correctly installed on every machine
2. Add Houdini bin path to every machine's PATH environment variable. The path should look like :
    ```C:\Program Files\Side Effects Software\Houdini 17.0.352\bin```

##### How to 'install' HTOT
1. Copy ```htot.hdanc``` to your Houdini asset library. Idealy this should be a shared directory for every machine.     For more details, check out : [sidefx.com/docs/houdini/assets/install](http://www.sidefx.com/docs/houdini/assets/install.html)
2. Copy  ```htot.py ``` to a directory accessible by every machine
3. Open houdini, go to the  ```/out/ ``` context and create a  ```HTOT ``` node.
4. Right click ```HTOT``` and choose ```Allow editing of contents```.
5. Dive in the node and in the ```Shell``` node you will need to modify the path for ```htot.py``` to where you copied it in step 2. Your shell command should look like :
    ```hython //MYSERVER/scripts/htot.py $HIPFILE `chs("../outputDriver")` `chs("../f1")` `chs("../f2")` `chs("../jobPriority")` ```
6. In the ```Assets``` menu, choose ```Save Asset``` > ```htot```. Your asset is now ready to be used.

##### How to use HTOT

1. Specify the frame range first. Default values are ```$FSTART``` and ```$FEND```
2. Specify the Output Driver (e.g. ```/out/mantra1```)
3. Specify the job priority

#### Known limitations
- At the moment, it is not possible to use HTOT if your scene uses ```$HIPNAME``` (e.g. in filecache nodes). You have to manually replace them with your scene name (except for Mantra nodes).
- The post-job cleanup won't delete ```$HIP/ifds/storage```. You will have to manually remove it after all your jobs are finished.
