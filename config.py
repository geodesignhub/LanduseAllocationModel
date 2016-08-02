apisettings = {
  "serviceurl": "http://local.dev:8000/api/v1/",
  "projectid": "23f85c2a201b8cfb",
  "apitoken": "bf6568eeebe620616f715753b4a70bd90b07d940",
  "username": "ufeusr1",
}

changeteamandsynthesis = {
	"changeteamid":1,
	"synthesisid":"264AH9GD48GKN6AK"
}
# linktype has to be evaluations, impacts or diagrams
evalsandpriority = [
	{"priority":1, "evalfilename": "input/HDH.geojson", "systemid":35, "name":"Industry"},
	]

featurefilesandpriority = [
	{"priority":1, "systemid":35, "name":"Industry","target": 10000, "allocationtype":"cluster"},
]
units = "hectares" # can only be acres or hectares
