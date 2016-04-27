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
from functools import partial
from shapely.ops import unary_union
from shapely import speedups
if speedups.available:
        speedups.enable()
class ShapesFactory():
	def multiPolytoFeature(self, mp):
		feats =[]
		for curCoords in mp['coordinates']:
			feats.append({'type':'Polygon','coordinates':curCoords})
		return feats

	def genFeature(self, coords):
		f = {}
		f['type']= 'Feature'
		f['properties']= {}
		f['geometry']= coords
		return f

	def createUnaryUnion(self, allAreas):
		''' Given a set of areas, this class constructs a unary union for them '''
		try:
			# Construct a unary_union assume that there are no errors in
			# geometry.
			allDsgnPlygons = unary_union(allAreas)
		except Exception, e1:
			# print "OK"
			# If there are errors while consutrcuting the union, examine the
			# geometries further to seperate
			s1All = []
			try:
			    s1Polygons = MultiPolygon([x for x in allAreas if (
			        x.geom_type == 'Polygon' or x.geom_type == 'MultiPolygon') and x.is_valid])
			    if s1Polygons:
			        s1All.append(s1Polygons)
			except Exception, e:
			    logging.error(
			        'SpatialimpactCalculator.py Error in CreateUnaryUnion Polygon: %s' % e)
			if s1All:
			    allDsgnPlygons = unary_union(s1All)
			else:
			    allDsgnPlygons = ''

		return allDsgnPlygons


	def generateShapeArea(self, feature, units):

		geom = feature['geometry']
		if len(geom['coordinates']) > 2:
		    geom['coordinates'] = geom['coordinates'][:2]
		lon, lat = zip(*geom['coordinates'][0])
		from pyproj import Proj
		pa = Proj("+proj=aea")
		# pa = Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
		x, y = pa(lon, lat)
		geomp = {"type": "Polygon", "coordinates": [zip(x, y)]}
		# # print (shape(geomp).area)
		s = shape(geomp)
		featureArea = (s.area)
		multiplier = 0.000247105 if areaunit == 'acres' else 0.001
		fArea = featureArea * multiplier
		return fArea

class RTreeHelper():
	def getNearestBounds(self, rtree, inputbounds, ):
		l = list(rtree.nearest(inputbounds, 1))
		return l

	def uniqify(self, seq):
		seen = set()
		seen_add = seen.add
		return [x for x in seq if not (x in seen or seen_add(x))]

	def extendBounds(self, origbounds, newboundslist):
		mins ={'minx':origbounds[0],'miny':origbounds[1]}
		maxs = {'maxx':origbounds[2],'maxy':origbounds[3]}
		for curbounds in newboundslist:
			mins['minx'] = float(curbounds[0]) if (mins['minx'] == 0) else min(float(curbounds[0]), mins['minx'])
			mins['miny'] = float(curbounds[1]) if (mins['miny'] == 0) else min(float(curbounds[1]), mins['miny'])
			maxs['maxx'] = float(curbounds[2]) if (maxs['maxx'] == 0) else max(float(curbounds[2]), maxs['maxx'])
			maxs['maxy'] = float(curbounds[3]) if (maxs['maxy'] == 0) else max(float(curbounds[3]), maxs['maxy'])

		return (mins['minx'], mins['miny'], maxs['maxx'], maxs['maxy'])

curPath = os.path.dirname(os.path.realpath(__file__))
# SOURCE_FILE_SHARE = os.path.join(curPath, 'input')

if __name__ == "__main__":
	# geodesign hub API client
	units = config.units
	print "Starting Allocation Model.."
	myAPIHelper = GeodesignHub.GeodesignHubClient(url = config.apisettings['serviceurl'], project_id=config.apisettings['projectid'], token=config.apisettings['apitoken'])
	# to genetate a shape out of a geometry.
	myShapesHelper = ShapesFactory()
	myRTreeHelper = RTreeHelper()
	# read the evaluations from the config file
	evalspriority = config.evalsandpriority
	# a list to store the shapes per areatype and system

	allEvalSortedFeatures = []
	# iterate over the evaluations

	for cureval in evalspriority:
		print "Preparing Evaluations.."

		# a dictionary to hold features
		evalfeatcollection = {'green2':[], 'green':[], 'yellow':[], 'red':[], 'red2':[]}
		evalfeatRtree = {'green2': Rtree(), 'green': Rtree() , 'yellow':Rtree(), 'red':Rtree(), 'red2':Rtree()}
		# open evaluation file
		filename = os.path.join(curPath, cureval['evalfilename'])
		with open(filename) as data_file:
		    geoms = json.load(data_file)

		# iterate over the geometry features.
		for curFeature in geoms['features']:
			shp = 0
			try:
				shp = asShape(curFeature['geometry'])
			except Exception as e:

				print explain_validity(shp)
				pass

			try:
				assert shp != 0
				bounds = shp.bounds
				featureArea = myShapesHelper.generateShapeArea(curFeature, units)
				fid = random.randint(1, 900000000)
				areatype = curFeature['properties']['areatype']
				evalfeatcollection[areatype].append({'id':fid,'shape':shp, 'bounds':bounds,'areatype':areatype,'area':featureArea, 'allocated':False})
				evalfeatRtree[areatype].insert(fid,bounds)
			except AssertionError as e:
				pass

		print "Processed {0} green2, {1} green, {2} yellow, {3} red and {4} red2 features from {5} system.".format(len(evalfeatcollection['green2']),len(evalfeatcollection['green']),len(evalfeatcollection['yellow']),len(evalfeatcollection['red']),len(evalfeatcollection['red2']),cureval['name'])

		# append the features to final list
		allEvalSortedFeatures.append({'rtree':evalfeatRtree,'system':cureval['system'],'priority':cureval['priority'], 'features':evalfeatcollection})

	# now all evaluations are in place, read the feature inputs
	syspriority = config.featurefilesandpriority
	# sort the dictionary so we read the most important first.
	syspriority = sorted(syspriority, key=itemgetter('priority'), reverse=True)
	# a list to
	sysAreaToBeAllocated =[]
	for cursysfeat in syspriority:
		print "Preparing Input Features.."
		filename = os.path.join(curPath, cursysfeat['featuresfilename'])
		with open(filename) as data_file:
		    geoms = json.load(data_file)
		allFeatShapes = []
		for curFeature in geoms['features']:
			shp = 0
			shparea =0
			try:
				shp = asShape(curFeature['geometry'])
			except Exception as e:
				print explain_validity(shp)
				pass

			try:
				assert shp != 0
				allFeatShapes.append(shp)
				ft =  json.loads(shapelyHelper.export_to_JSON(curFeature['geometry']))
				ft = myShapesHelper.genFeature(ft)
				shparea = myShapesHelper.generateShapeArea(ft, units)

			except AssertionError as e:
				pass
		if allFeatShapes and cursysfeat['allocationtype'] =='random':
			allShapes = [myShapesHelper.createUnaryUnion(allFeatShapes)]

		else:
			allShapes =[]
		print "Processed {0} features from {1} system.".format(len(allFeatShapes),cursysfeat['name'])
		sysAreaToBeAllocated.append({'name':cursysfeat['name'],'system':cursysfeat['system'], 'priority':cursysfeat['priority'], 'type':cursysfeat['allocationtype'], 'targetarea':cursysfeat['target'], 'shapes':allShapes,'area':shparea, 'alreadyallocated': Rtree()})

	# All data has been setup
	sysAreaToBeAllocated = sorted(sysAreaToBeAllocated, key=itemgetter('priority'))
	colorPrefs = ('green2', 'green', 'yellow')#, 'red', 'red2')

	syscounter = 0
	#create allocated geoms rtree



	for curSysAreaToBeAllocated in sysAreaToBeAllocated:
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

					if iFeats and curSysAreaToBeAllocated['type'] == 'random':

						random.shuffle(iFeats)


					for curiFeat in iFeats: # iterate over the ids
						if totalIntersectedArea < curSysAreaToBeAllocated['targetarea']:
							curevalfeat = (item for item in evalfeatures['features'][curAllocationColor] if item["id"] == curiFeat).next() # get the evaluation featre with the id
							try:
								# TODO: Try this for two systems.
								assert syscounter != 0
								# get a list of rTrees that have lower priority than this system.
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


			# if totalIntersectedArea < curSysAreaToBeAllocated['targetarea']:
			# # all areas that intersect have been allocated if there is more to be allocated, allocate now till everything is allocated in this color
			# 	curEFeatRtree = evalfeatures['rtree'][curAllocationColor]
			# 	totalEvalFeats = evalfeatures['features'][curAllocationColor]
			# 	sortedNearestFeats = []
			# 	sortedFeatCounter =0
			# 	while sortedFeatCounter != len(totalEvalFeats):
			# 		nearestFeats =  myRTreeHelper.getNearestBounds(curEFeatRtree, lastfeatbounds)
			# 		sortedNearestFeats.extend(nearestFeats)
			# 		allNearestBounds  =[]
			# 		for curNearestFeat in nearestFeats:
			# 			i = (item for item in evalfeatures['features'][curAllocationColor] if item["id"] == random.choice(nearestFeats)).next()
			# 			allNearestBounds.append(i['bounds'])
			# 		lastfeatbounds = myRTreeHelper.extendbounds(allNearestBounds)
			# 		sortedNearestFeats = myRTreeHelper.uniqify(sortedNearestFeats)
			# 		print sortedNearestFeats
			# 		sortedFeatCounter = len(sortedNearestFeats)
			# 		# print sortedFeatCounter, len(totalEvalFeats)


			# 	for cursortedFeat in sortedNearestFeats:
			# 		curevalfeat = (item for item in evalfeatures['features'][curAllocationColor] if item["id"] == cursortedFeat).next()

			# 		if curevalfeat['allocated'] == True:
			# 			pass

			# 		else:
			# 			# 	allocate
			# 			curevalfeat['allocated'] == True
			# 			# append to geoms
			# 			totalAllocatedGeoms.insert(curevalfeat['id'],curevalfeat['bounds'])
			# 			alreadyAllocatedFeats.append(curevalfeat['shp'])
			# 			totalIntersectedArea  += curevalfeat['area']

		print "Allocated " + str(totalIntersectedArea) + " Acres"
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
		oppath =  os.path.join(curPath, 'output',str(curSysAreaToBeAllocated['name'])+'-op.geojson')
		with open(oppath, 'w') as outFile:
			json.dump(transformedGeoms , outFile)

	print "Finished Allocations"
