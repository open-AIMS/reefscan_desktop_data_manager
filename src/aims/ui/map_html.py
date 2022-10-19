from reefscanner.basic_model.photo_csv_maker import track

html_str = """
<!DOCTYPE html>
<html>
<head>
	
	<title>Quick Start - Leaflet</title>

	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	
	<link rel="shortcut icon" type="image/x-icon" href="docs/images/favicon.ico" />

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js" integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==" crossorigin=""></script>


	
</head>
<body>



<div id="mapid" style="width: 100%; height: 100%; position: absolute; top:0; bottom:0"></div>
<script>

	var mymap = L.map("mapid");
	
	googleSat = L.tileLayer("http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",{
    maxZoom: 100,
    subdomains:["mt0","mt1","mt2","mt3"]
	});
	googleSat.addTo(mymap);
	
	var latlngs = ___PASTE_TRACK_HERE___
	
	
	var polyline = L.polyline(latlngs, {color: 'red'}).addTo(mymap);

	// zoom the map to the polyline
	mymap.fitBounds(polyline.getBounds());
	if (mymap.getZoom() > 14) {
	    mymap.setZoom(14)
	}
	


</script>



</body>
</html>

"""


def map_html_str(folder, samba):
    track_str = str(track(folder, samba))
    if track_str is None:
        return None
    return html_str.replace("___PASTE_TRACK_HERE___", track_str)
