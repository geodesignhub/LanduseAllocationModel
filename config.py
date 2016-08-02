# configure the API settings with the correct project id and username
apisettings = {
  "serviceurl": "http://local.dev:8000/api/v1/",
  "projectid": "1f2c2d16467905ed",
  "apitoken": "5e8d2389ee19a18b53a85de40a4e1cc012b318c5",
  "username": "ufeusr1",
}
# enter the correct change team and synthesis ID
changeteamandsynthesis = {
	"changeteamid":5,
	"synthesisid":"BIEBPD9132BJGC46"
}
# enter the details of the gridded evaluation files and the correct system ID and priority.
evalsandpriority = [
	{"priority":1, "evalfilename": "input-evaluations/HDH.geojson", "systemid":17, "name":"Housing"},
	]

featurefilesandpriority = [
	{"priority":1, "systemid":17, "name":"Housing","target": 10000, "allocationtype":"cluster"},
]
units = "hectares" # can only be acres or hectares
allocationrunnumber = 0 # give a run number, it will be appended to the upload