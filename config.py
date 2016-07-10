apisettings = {
  "serviceurl": "http://local.dev:8000/api/v1/",
  "projectid": "91cb24d7cd1feb2b",
  "apitoken": "55006fd988b3fd3235096b5bac079207b5c38aed",
  "username": "ufeusr1",
}
changeteamandsynthesis = {
	"changeteamid":1,
	"synthesisid":"afea"
}
# linktype has to be evaluations, impacts or diagrams
evalsandpriority = [
	{"priority":1, "evalfilename": "input-evaluations/commind-final.geojson", "systemid":1, "name":"Industry"},
	{"priority":2, "evalfilename": "input-evaluations/housing-final.geojson", "systemid":2, "name":"Housing"},
	{"priority":3, "evalfilename": "input-evaluations/ldhousing-final.geojson", "systemid":3,"name":"Low Density Housing"}
	]

featurefilesandpriority = [
	{"priority":1, "systemid":1, "name":"Industry","target": 10000, "allocationtype":"cluster"},
	{"priority":2, "systemid":2, "name":"Housing", "target":7000, "allocationtype":"cluster"},
	{"priority":3, "systemid":3, "name":"LD Housing", "target":10000, "allocationtype":"random"}
]
units = "hectares" # can only be acres or hectares
