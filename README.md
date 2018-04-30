# Legger

Toolset for assigning 'legger' profiles to channels (hydro objects), based on
the water gradiant calculated with 3di model results

## Installation

Steps for installation of this QGIS plugin:

1. Make sure the 64-bit version of QGIS 2.18.x is installed

2. Install the 3di QGIS plugin. See installation instruction on:
   https://github.com/nens/threedi-qgis-plugin/wiki

3. download shapely from the site:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
   Probably you need the version Shapely‑1.6.xxx‑cp27‑cp27m‑win_amd64.whl

4. Find out the program root of your QGIS installation or OSGeo4w64 installation

5. start a command prompt (cmd) and go to the QGIS or OSgeo4w64 root directory (cd xxxx)
   First remove the old version of shapely
   ```
    del apps\python27\lib\site-packages\shapely.pth
   ```
   and install new version
   ```
   bin\python -m pip --install --force-reinstall <<path to downloaded whl file>>
   ```

6. Copy the legger tool directory (the directory containing this readme) to the qgis plugin folder
   This folder is situated under:
   <<user directory>>\.qgis\python\plugins

## development remarks

after adding an icon in the media folder and link in the file resources.qrc, generate a new resources.py with the command:
```
pyrcc4 -o resources.py resources.qrc
```
