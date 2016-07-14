import config
import GeodesignHub, shapelyHelper
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape, mapping, shape, asShape
import os, sys, requests, geojson
import json, pyproj
import string, random
from operator import itemgetter
from rtree import Rtree
from shapely.validation import explain_validity
from tqdm import tqdm
from shapely.ops import unary_union
from shapely import speedups
from sys import version_info

if speedups.available:
	speedups.enable()
'''
Geodesign Hub Compatible Land Use Allocation Model

This model takes in gridded evaluation files and input features from Geodesign Hub (www.geodesignhub.com) and allocates them. 

Projection: Geodesign Hub uses EPSG 4326 / WGS 94 (http://epsg.io/4326) and all GeoJSON files should be in that projection.

This is the main file the other files are as follows: 
config.py: This file contains the configuration and input evaluation and features files and also settings for system prirority. 
GeodesignHub.py : This is the Geodesign Hub client written in Python, it is useful for interacting with the Geodesign Hub API. 
shapelyHelper.py: This file is a helper class for Shapely (https://pypi.python.org/pypi/Shapely) the Python library used for spatial analysis. 
'''

import sys

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
	Source : http://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input 
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
class ShapesFactory():
	''' A class to help in geometry operations '''
	def multiPolytoFeature(self, mp):
		''' Given Multipolygons, convert them into single polygon '''
		feats =[]
		for curCoords in mp['coordinates']:
			feats.append({'type':'Polygon','coordinates':curCoords})
		return feats

	def genFeature(self, coords):
		''' Given a set of coordinates return a Feature, useful when converting from Multipolygon -> Polygon '''
		f = {}
		f['type']= 'Feature'
		f['properties']= {}
		f['geometry']= coords
		return f

	def createUnaryUnion(self, allAreas):
		''' Given a set of areas, this method constructs a unary union for them '''
		try:
			# Construct a unary_union assume that there are no errors in
			# geometry.
			allDsgnPlygons = unary_union(allAreas)
		except Exception, e1:
			# If there are errors while consutrcuting the union, examine the
			# geometries further to seperate to just valid polygons. To avoid this error, 
			# ensure that the evaluation features are topologically correct, usually use a 
			# Geometry checker in GIS tools. 
			s1All = []
			try:
			    s1Polygons = MultiPolygon([x for x in allAreas if (
			        x.geom_type == 'Polygon' or x.geom_type == 'MultiPolygon') and x.is_valid])
			    if s1Polygons:
			        s1All.append(s1Polygons)
			except Exception, e:
			    logging.error('Error in CreateUnaryUnion Polygon: %s' % e)
			if s1All:
			    allDsgnPlygons = unary_union(s1All)
			else:
			    allDsgnPlygons = ''

		return allDsgnPlygons


	def generateShapeArea(self, feature, units):
		''' Given a feature compute the area in the given units. Acceptable units are acres or hectares. 
		This function converts the feature in AEA (http://mathworld.wolfram.com/AlbersEqual-AreaConicProjection.html) to approximate
		the total area. '''
		geom = feature['geometry']
		if len(geom['coordinates']) > 2:
		    geom['coordinates'] = geom['coordinates'][:2]
		lon, lat = zip(*geom['coordinates'][0])
		from pyproj import Proj
		pa = Proj("+proj=aea")
		# alternative WGS 1984
		# pa = Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
		x, y = pa(lon, lat)
		geomp = {"type": "Polygon", "coordinates": [zip(x, y)]}
		s = shape(geomp)
		featureArea = (s.area)
		# default is hectares, if in acres, convert by using the multiplier. 
		multiplier = 0.000247105 if units == 'acres' else 0.001
		fArea = featureArea * multiplier
		return fArea

class RTreeHelper():
	'''This class has helper functions for the RTree Spatial Index. (https://pypi.python.org/pypi/Rtree/) '''
	def getNearestBounds(self, rtree, inputbounds,):
		''' Given a set of input bounds, return a list of nearest bounds from the index ''' 
		l = list(rtree.nearest(inputbounds, 1))
		return l

	def uniqify(self, seq):
		''' Given a set of bounds keep only the uniques '''
		seen = set()
		seen_add = seen.add
		return [x for x in seq if not (x in seen or seen_add(x))]

	def extendBounds(self, origbounds, newboundslist):
		''' Given two bounds (in WGS 1984) lant long extend the bounds '''
		mins ={'minx':origbounds[0],'miny':origbounds[1]}
		maxs = {'maxx':origbounds[2],'maxy':origbounds[3]}
		for curbounds in newboundslist:
			mins['minx'] = float(curbounds[0]) if (mins['minx'] == 0) else min(float(curbounds[0]), mins['minx'])
			mins['miny'] = float(curbounds[1]) if (mins['miny'] == 0) else min(float(curbounds[1]), mins['miny'])
			maxs['maxx'] = float(curbounds[2]) if (maxs['maxx'] == 0) else max(float(curbounds[2]), maxs['maxx'])
			maxs['maxy'] = float(curbounds[3]) if (maxs['maxy'] == 0) else max(float(curbounds[3]), maxs['maxy'])

		return (mins['minx'], mins['miny'], maxs['maxx'], maxs['maxy'])

# Set the current path so that the evaluation and feature folders can be reads.
curPath = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":

	# Read and set the units. 
	print "Starting Allocation Model.."
	units = config.units
	# Set up the API Client
	myAPIHelper = GeodesignHub.GeodesignHubClient(url = config.apisettings['serviceurl'], project_id=config.apisettings['projectid'], token=config.apisettings['apitoken'])
	# Download the features file from the given synthesis ID 
	evalspriority = config.evalsandpriority
	cteamid = config.changeteamandsynthesis['changeteamid']
	
	synthesisid = config.changeteamandsynthesis['synthesisid']
	try:
		synthesischeck = myAPIHelper.get_synthesis(teamid = cteamid, synthesisid = synthesisid)
	except requests.ConnectionError:
		print "Could not connect to Geodesign Hub API service."
		sys.exit(0)
	c = synthesischeck.json()
	print "Downloading project features from the synthesis..."
	try:
		assert c['status'] != "API Endpoint not found." 
	except AssertionError as e: 
		print "Invalid change team or synthesis id."
	inputdirectory = os.path.join(curPath,'input-features')
	if not os.path.exists(inputdirectory):
		os.makedirs(inputdirectory)
	for sp in evalspriority:
		cursysid = sp['systemid']
		fname = sp['name']
		# get the projects for this system from the synthesis ID.
		try:
			projectsdata = myAPIHelper.get_synthesis_system_projects(teamid =cteamid , sysid =cursysid, synthesisid = synthesisid)
		except requests.ConnectionError:
			print "Could not connect to Geodesign Hub API service."
			sys.exit(0)
		# write the file
		featfilename = fname +'.geojson'
		fpath = os.path.join(curPath,'input-features', fname +'.geojson')
		f = open(fpath, 'w')
		f.write(projectsdata.text)
		f.close()
		sp['featuresfilename'] = featfilename
	print "Features downloaded in the input-features directory.."
	# Create instances of our helper classes
	myShapesHelper = ShapesFactory()
	myRTreeHelper = RTreeHelper()
	# read the evaluations from the config file
	evalspriority = config.evalsandpriority
	# a ordered list to store the shapes per areatype and system. # TODO: User a OrderedDict 
	allEvalSortedFeatures = []
	# iterate over the evaluations
	# iterate over the evaluations
	print "Preparing Evaluations.."
	opfiles = []
	for cureval in tqdm(evalspriority):
		# a dictionary to hold features, we will ignore the red and red2 since allocation should not happen here. 
		evalfeatcollection = {'green3':[],'green2':[], 'green':[]}
		# A dictionary to store the index of the features. 
		evalfeatRtree = {'green3':Rtree(),'green2': Rtree(), 'green': Rtree()}
		# open evaluation file
		filename = os.path.join(curPath, cureval['evalfilename'])
		with open(filename) as data_file:
			try:
				geoms = json.load(data_file)
			except Exception as e: 
				print "Error in loading evaluation geometries, please check if it is a valid JSON."
				sys.exit(0)

		# iterate over the geometry features.
		for curFeature in geoms['features']:
			shp = 0
			featureArea=0
			try:
				# convert the JSON feature in to Shape using Shapely's asShape. 
				shp = asShape(curFeature['geometry'])
			except Exception as e:
				# if there is a error in conversion go to the next shape. 
				print explain_validity(shp)
				pass
			try:
				assert shp != 0
				# get the bounds of the shape
				bounds = shp.bounds
				# generate the area of the shape
				featureArea = myShapesHelper.generateShapeArea(curFeature, units)
				# generate a random id for the shape
				fid = random.randint(1, 900000000)
				# check the areatype
				areatype = curFeature['properties']['areatype']
				if areatype in evalfeatcollection.keys():
					# input the shape and details in the collections
					evalfeatcollection[areatype].append({'id':fid,'shape':shp, 'bounds':bounds,'areatype':areatype,'area':featureArea, 'allocated':False})
					# insert the bounds and id into the rtree, the id is used to get the shape later. 
					evalfeatRtree[areatype].insert(fid,bounds)
			except AssertionError as e:
				pass

		print "Processed {0} green3, {1} green2, {2} green from {3} system.".format(len(evalfeatcollection['green3']), len(evalfeatcollection['green2']),len(evalfeatcollection['green']),cureval['name'])

		# Once all the evaluation features are processed, then insert it into the sorted features list including the rtree index. 
		allEvalSortedFeatures.append({'rtree':evalfeatRtree,'system':cureval['systemid'],'priority':cureval['priority'], 'features':evalfeatcollection})
		# Proceed to the next evaluation file.

	# now all evaluations are in place, read the feature inputs
	# sort the dictionary so we read the most important first.
	syspriority = sorted(syspriority, key=itemgetter('priority'), reverse=True)
	# a list to hold the processed features and their details. 
	sysAreaToBeAllocated =[]
	# iterate over the system files. 
	print "Preparing Input Features.."
	for cursysfeat in tqdm(syspriority):
		
		filename = os.path.join(curPath, cursysfeat['featuresfilename'])
		with open(filename) as data_file:
			try: 
			    geoms = json.load(data_file)
			except Exception as e: 
				print "Invalid geometries in the file, please check that it is valid JSON."
				sys.exit(0)
		# a list to hold all shapes in this feature file
		allFeatShapes = []
		# iterate over the read features
		for curFeature in geoms['features']:
			shp = 0
			# set the default shape area to be 0
			totalarea = 0
			try:
				# Convert the feature into a shape. 
				shp = asShape(curFeature['geometry'])
			except Exception as e:
				#if there is a error in converting to shape, describe the error. 
				print explain_validity(shp)
				pass
			try:
				assert shp != 0
				# add the shape to our features list
				allFeatShapes.append(shp)
				totalarea += myShapesHelper.generateShapeArea(curFeature, units)

			except AssertionError as e:
				pass
		# if allFeatShapes and cursysfeat['allocationtype'] =='random':
		allShapes = [myShapesHelper.createUnaryUnion(allFeatShapes)]

		print "Processed {0} features from {1} system.".format(len(allFeatShapes),cursysfeat['name'])
		sysAreaToBeAllocated.append({'name':cursysfeat['name'],'system':cursysfeat['system'], 'priority':cursysfeat['priority'], 'type':cursysfeat['allocationtype'], 'targetarea':cursysfeat['target'], 'shapes':allShapes,'totalarea':totalarea, 'alreadyallocated': Rtree()})

	# All data has now been setup, we start the allocaiton process. 
	sysAreaToBeAllocated = sorted(sysAreaToBeAllocated, key=itemgetter('priority'))
	colorPrefs = ('green3','green2', 'green') # there is no preference for reds
	# a counter for systems. 
	syscounter = 0
	# iterate over the features which are sorted by priority.
	print "Starting Allocations..." 
	for curSysAreaToBeAllocated in tqdm(sysAreaToBeAllocated):
		print "Allocating for " + curSysAreaToBeAllocated['name']
		alreadyAllocatedFeats = [] # a object to hold already allocated features for this system.
		sysid = curSysAreaToBeAllocated['system'] # the id of the current system
		evalfeatures = (item for item in allEvalSortedFeatures if item["system"] == sysid).next() # get the evaluation feature object.
		totalIntersectedArea = 0 # variable to hold the intersected area.
		curSysPriority = curSysAreaToBeAllocated['priority']
		curSysName = curSysAreaToBeAllocated['name']
		for curAllocationColor in colorPrefs: # iterate over the colors
			curEFeatRtree = evalfeatures['rtree'][curAllocationColor] #get the rtree of the eval color
			# totalEvalFeats = evalfeatures['features'][curAllocationColor]
			modifiedevalFeats =[] # a list to hold the evaluation features that have allocated = true for this color
			if totalIntersectedArea < curSysAreaToBeAllocated['targetarea']:
				for curFeat in curSysAreaToBeAllocated['shapes']: # iterate over the input shapes
					bnds = curFeat.bounds # get the bounds
					# check if there is a intersection
					iFeats = [n for n in curEFeatRtree.intersection(bnds)] # check how many eval features intersect with the input
					if iFeats and curSysAreaToBeAllocated['type'] == 'random': # once the evaluation features are selected, shuffle them so that the allocaiton can be random.
						random.shuffle(iFeats)

					for curiFeat in iFeats: # iterate over the evaluation features. 
						if totalIntersectedArea < curSysAreaToBeAllocated['targetarea']: # if the area of intersectio is less then the target area. 
							curevalfeat = (item for item in evalfeatures['features'][curAllocationColor] if item["id"] == curiFeat).next() # get the evaluation featre with the id
							try:
								# Since this is the first system, create a allreaded allocated RTree
								assert syscounter != 0
								# get a list of rTrees that have lower priority than this system. example if the current sys priority is 2, get the priority 1 already allocated features. This is to ensure that 
								prevRTrees = [x['alreadyallocated'] for x in sysAreaToBeAllocated if x['priority'] < curSysPriority]
								l = []
								for prevRTree in prevRTrees:
									l.extend(list(prevRTree.intersection(curevalfeat['bounds'])))
								if l:
									pass
								else:
									intersection = 0
									try:
										intersection = curevalfeat['shape'].intersection(curFeat)
									except Exception as e:
										pass
									if intersection:
										curSysAreaToBeAllocated['alreadyallocated'].insert(curevalfeat['id'],curevalfeat['bounds'])
										alreadyAllocatedFeats.append(intersection)
										ft =  json.loads(shapelyHelper.export_to_JSON(intersection))
										ft = myShapesHelper.genFeature(ft)
										if ft['geometry']['type'] == 'MultiPolygon':
											ft = myShapesHelper.multiPolytoFeature(ft['geometry'])
											for feat in ft:
												feat = myShapesHelper.genFeature(feat)
												area += myShapesHelper.generateShapeArea(feat, units)
										else:
											area = myShapesHelper.generateShapeArea(ft, units)
										totalIntersectedArea += area
										curevalfeat['allocated'] = True
										modifiedevalFeats.append(curevalfeat)
							except AssertionError as ae:
									intersection = 0
									try:
										intersection = curevalfeat['shape'].intersection(curFeat)
									except Exception as e:
										pass

									if intersection:
										curSysAreaToBeAllocated['alreadyallocated'].insert(curevalfeat['id'],curevalfeat['bounds'])
										alreadyAllocatedFeats.append(intersection)
										f1 =  json.loads(shapelyHelper.export_to_JSON(intersection))
										f1 = myShapesHelper.genFeature(f1)
										if f1['geometry']['type'] == 'MultiPolygon':
											f1 = myShapesHelper.multiPolytoFeature(f1['geometry'])
											for feat in f1:
												feat = myShapesHelper.genFeature(feat)
												area += myShapesHelper.generateShapeArea(feat, units)
										else:
											area = myShapesHelper.generateShapeArea(f1, units)

										totalIntersectedArea += area
										curevalfeat['allocated'] = True
										modifiedevalFeats.append(curevalfeat)

			for curmodifiedFeat in modifiedevalFeats:
				evalfeatures['features'][curAllocationColor] = [x for x in evalfeatures['features'][curAllocationColor] if x['id'] != curmodifiedFeat['id']]
				evalfeatures['features'][curAllocationColor].append(curmodifiedFeat)

		print "Allocated " + str(totalIntersectedArea) + " " + units
		print "Writing Output file.."
		newGeoms = []
		for curAllocation in alreadyAllocatedFeats:
			cf ={}
			f = json.loads(shapelyHelper.export_to_JSON(curAllocation))
			cf['type']= 'Feature'
			cf['properties']= {}
			cf['geometry']= f
			# cf['properties']['allocated'] = 1
			newGeoms.append(cf)

		syscounter+= 1
		transformedGeoms = {}
		transformedGeoms['type'] = 'FeatureCollection'
		transformedGeoms['features'] = newGeoms
		
		outputdirectory = os.path.join(curPath,'output')
		if not os.path.exists(outputdirectory):
			os.makedirs(outputdirectory)
		oppath =  os.path.join(curPath, 'output',str(curSysAreaToBeAllocated['name'])+'-op.geojson')
		with open(oppath, 'w') as outFile:
			json.dump(transformedGeoms , outFile)
		opfiles.append({'allocationfile':oppath,'sysname':curSysAreaToBeAllocated['name'],'sysid':curSysAreaToBeAllocated['systemid']})
	print "Finished Allocations"
	
	uploadOK = query_yes_no("Upload allocation outputs to the Project?")
	if uploadOK: 
		# read the allocated file
		for curopfile in opfiles:
			with open(curopfile, 'r') as f:
				# set the system number 
				allocatedFeats = f.read()
				
			allocatedFeats = json.loads(allocatedFeats)
			print "Uploading allocations as diagrams.."
			uploadfilename = curSysAreaToBeAllocated['name'] +' v'+ config.allocationrunnumber
			upload = myAPIHelper.post_as_diagram(geoms = allocatedFeats, projectorpolicy= 'project',featuretype = 'polygon', description=uploadfilename, sysid = curopfile['sysid'] )
			print upload.text
