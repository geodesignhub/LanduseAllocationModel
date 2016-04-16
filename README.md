##Geodesign Hub compatible Landuse Allocation Model
A demand-based, evaluation-weighted, geodesign designated land use allocation model

###Overview
This repository is a simple demand based evaluation weighted land use allocation model. It takes in a evaluation geojson file from Geodesign Hub and 


####Pseudocode
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
Install all dependencies on your computer (Rree, 
```
pip install requirements.txt
```
This should install Shapely and RTree and requests libraries. For Windows users please download binaries from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).

### Update config.py
Config.py has a sample configuration, modify it for your purposes. 
