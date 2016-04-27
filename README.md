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
- Start with Green2 (most suitable / preferred) location in the evaluation map. 
- Intersect the current feature with the evaluation, allocate if intersected
  - If not intersected move to the next designed feature or evaluation feature
- Contintue till either out of features or target reached. 


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
For the purposes of allocation the evaluation GeoJSON files built for Geodesign Hub Systems need to be split into a tiny grid. This can be done in a regular GIS software. The grid size should depend on the kind of area that you are studying. 


#### Update config.py
Config.py has a sample configuration, modify it for your purposes. 
