# configure the API settings with the correct project id and username
apisettings = {
  "serviceurl": "http://local.dev:8000/api/v1/",
  "projectid": "23f85c2a201b8cfb",
  "apitoken": "bf6568eeebe620616f715753b4a70bd90b07d940",
  "username": "ufeusr1",
}
# enter the correct change team and synthesis ID
changeteamandsynthesis = {
	"changeteamid":1,
	"synthesisid":"0JG9B4J0OEOBEM38"
}
# enter the details of the gridded evaluation files and the correct system ID and priority.
evalsandpriority = [
	{"target": 10000,"priority":1, "evalfilename": "input-evaluations/commind-final.geojson", "systemid":35, "name":"Industry","allocationtype":"cluster"},
	{"target":7000,"priority":2, "evalfilename": "input-evaluations/housing-final.geojson", "systemid":2, "name":"Housing","allocationtype":"cluster"},
	{ "target":10000,"priority":3, "evalfilename": "input-evaluations/ldhousing-final.geojson", "systemid":3,"name":"Low Density Housing", "allocationtype":"random"}
	]

units = "hectares" # can only be acres or hectares
allocationrunnumber = 0 # give a run number, it will be appended to the upload