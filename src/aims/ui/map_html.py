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

     function makePopup(image) {
        return image +'<br/><a href=file:///' + image + ' target="_">a</a>';
    }
     var icon = L.divIcon({
      className: 'map-magnitude-icon',
       iconAnchor: [0, 0],
      popupAnchor: [0, 0],
      iconSize: [10, 10],
       html: 
        `
        <div style=
        "background-color: #00FFFF;
      width: 10px;
      height: 10px;
      display: block;
      transform: translate(-50%,-50%);
      position: relative;
      border-radius: 100%;
      border: 1px solid #FFFFFF;
      opacity: 0.7;">
        </div>
        `
    });
      
	var mymap = L.map("mapid");
	
	googleSat = L.tileLayer("http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",{
    maxZoom: 100,
    subdomains:["mt0","mt1","mt2","mt3"]
	});
	googleSat.addTo(mymap);
	
	var latlngs = ___PASTE_TRACK_HERE___
	
	
//	 var polyline = L.polyline(latlngs, {color: 'red'}).addTo(mymap);
	var markersLayer = L.featureGroup();
    mymap.addLayer(this.markersLayer);
    for (const l of latlngs) {
        const marker = L.marker([l[0], l[1]]);
        marker.setIcon(icon)
        marker.addTo(markersLayer);
        marker.bindPopup(makePopup(l[2]))
	}
	
	


	// zoom the map to the polyline
	bounds = markersLayer.getBounds()
	if ((bounds._northEast.lat - bounds._southWest.lat) < 0.00001) {
		bounds._southWest.lat = bounds._southWest.lat + 0.00001
	}
	if ((bounds._northEast.lng - bounds._southWest.lng) < 0.00001) {
		bounds._southWest.lng = bounds._southWest.lng + 0.00001
	}

	mymap.fitBounds(bounds);
	
	if (mymap.getZoom() > 14) {
	    mymap.setZoom(14)
	}
	


</script>



</body>
</html>

"""



def map_html_str(folder, samba):
    try:
        try:
            _track = track(folder, samba)
            print(len(_track))
        except:
            _track = None

        if _track is None or len(_track) < 2:
            return "<html>No Map</html"

        track_str = str(_track)
        return html_str.replace("___PASTE_TRACK_HERE___", track_str)
    except Exception as e:
        raise UserWarning(e)

