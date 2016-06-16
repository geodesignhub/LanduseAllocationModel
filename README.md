##Geodesign Hub compatible Landuse Allocation Model
A demand-based, evaluation-weighted, geodesign designated land use allocation model

###Overview
This repository is a simple demand based evaluation weighted land use allocation model. It takes in a gridded evaluation geojson file and features for "urban" type landuses from Geodesign Hub and allocates them based on a priority and also target (in acres or hectares) allocation. 

####Pseudocode logic
- Iterate over all features / polygons of a evaluation map
  - Check if it is Red2, Red, Yellow, Green or Green2 and store it in a rtree
  - Store the id, polyogn area and color classification of the evaluation layer.
- Sort the stored ids for each evaluation map grouped by the color
- Get designed features from Geodesign Hub
- Start with the first priority evaluation and first priority system.
- Start with Green2 (most feasable) location in the evaluation map. 
- Intersect the current feature with the evaluation, allocate if intersected
  - If not intersected move to the next designed feature or evaluation feature
- Contintue to the next most suitable (green) and next most capable (yello) till either there are no more features or target reached. Do not allocate on red or red2 


### Prerequisites
Install all dependencies on your computer (Rree and Shapely)
```
pip install requirements.txt
```
This should install Shapely and RTree and requests libraries. For Windows users please download binaries from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).

###Usage
Setup the evaluation maps, edit the config file with your paths and inputs and then run the following command:
```python
python GDHAllocationModel.py
```

###Inputs
There are two inputs for this script both configured through config.py
- Gridded evaluation files (see below)
- Feature colleciton input of selected diagrams (projects only) that can be downloaded via the Geodesign Hub [API](http://www.geodesignsupport.com/kb/get-methods/)

###Outputs
In the output directory, the script will produce a allocated output for each of the systems based on the targets setup in the config file. For the moment, you can ignore the allocation type option. The output will be produced in GeoJSON and in EPSG 4326 projection. It can be uploaded back to Geodesign Hub

#### Creating gridded Evaluation GeoJSON
For the purposes of allocation the evaluation GeoJSON files built for Geodesign Hub Systems need to be split into a tiny grid. This can be done in a regular GIS software. The grid size should depend on the kind of area that you are studying. Following are the steps: 

1. Create a raster of the area from your vectorial maps, with resolution of 250 m (or less) and with all the cells with the same color (grid value);
2. Convert from raster to point;
3. Apply "Create Thiessen Polygons" using the value of the grid that are all the same. It works like Delaunay distributions and constructs regular quadrangular grids, as all the points have the same value and are distributed in regular grid.
4. Intersect with the study area boundaries to remove shapes that are not within the study area;
5. Using the points created in step 2, "extract values to points" from each raster of the evaluation maps. Use the same file of points, to make sure the points will always be in the same place. You may have to change the name of the column it creates because each time you extract the values from a raster. Every time you extract values from a raster it creates a column with the same name and if the column name already exists, it can be a problem.

Thank you to [Prof. Ana Clara Moura](http://geoproea.arq.ufmg.br/equipe/prof-ana-clara-mourao-moura) for these instructions. 

#### Update config.py
Config.py has a sample configuration, modify it for your purposes. 

#### Video tutorial
[![YouTube Video tutorial](http://i.imgur.com/3KNhYft.png)](https://www.youtube.com/watch?v=QFbOM5T2eQQ)

#### LICENSE
The MIT License (MIT)

Copyright (c) 2016 Hrishikesh Ballal

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
