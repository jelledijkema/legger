# Legger

Toolset for assigning 'legger' profiles to channels (hydro objects), based on
the water gradiant calculated with 3di model results

## Installation

Steps for installation of this QGIS plugin:

1. Make sure the 64-bit version of QGIS 2.18.x is installed

2. Make sure you have Python 2.7.x installed. QGIS comes with a Python interpreter, 
   but in practice it might work best if there is a seperate Python installed.

3. Install the 3di QGIS plugin. See installation instruction on:
   https://github.com/nens/threedi-qgis-plugin/wiki

4. The following Python packages are required for the tool, but don't come with every QGIS package:
   - shapely
   - pandas
   - descartes
   If these packages indeed are missing, download the wheels for pandas 0.23.4 and descartes 1.1.0
   Download shapely from the site:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
   Probably you need the version Shapely‑1.6.xxx‑cp27‑cp27m‑win_amd64.whl

5. Find out the program root of your QGIS installation or OSGeo4w64 installation

6. It might be required to update pip before installing pandas and descartes: 
   ```
    python -m pip install --upgrade pip
   ```
   Then:
   ```
    python -m pip install path/to/wheel
   ```
   or type in command prompt, and replace between <..> with package name (like pandas)
   ```
    python -m pip install <package>
   ```
   
7. For installing shapely start a command prompt (cmd) and go to the QGIS or OSgeo4w64 root directory (cd xxxx)
   First remove the old version of shapely
   ```
    del apps\python27\lib\site-packages\shapely.pth
   ```
   and install new version
   ```
   bin\python -m pip --install --force-reinstall <<path to downloaded whl file>>
   ```

8. Copy the legger tool directory (the directory containing this readme) to the qgis plugin folder
   This folder is situated under:
   <<user directory>>\.qgis\python\plugins
   
9. If the plugin doesn't recognize packages (like the just installed pandas and descartes) you can copy the packages to:
   <<user directory>>\.qgis\python\plugins\legger\external

## development remarks

after adding an icon in the media folder and link in the file resources.qrc, generate a new resources.py with the command:
```
pyrcc4 -o resources.py resources.qrc
```
