import logging

from reefscanner.basic_model.photo_csv_maker import track, make_photo_csv

from aims.model.cots_detection_list import CotsDetectionList

logger = logging.getLogger("")
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

     function makePopup(msg) {
        return msg ;
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
      width: 7px;
      height: 7px;
      display: block;
      transform: translate(-50%,-50%);
      position: relative;
      border-radius: 100%;
      border: 0px solid #FFFFFF;
      opacity: 0.7;">
        </div>
        `
    });
	
     var red_square = L.divIcon({
      className: 'map-magnitude-icon',
       iconAnchor: [0, 0],
      popupAnchor: [0, 0],
      iconSize: [10, 10],
       html: 
        `
 <div style=
        "background-color: #FF0000;
      width: 10px;
      height: 10px;
      display: block;
      transform: translate(-50%,-50%);
      position: relative;
      border: 0px solid #FFFFFF;
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
	var cots_points = ___PASTE_COTS_HERE___
		
	
//	 var polyline = L.polyline(latlngs, {color: 'red'}).addTo(mymap);
	var markersLayer = L.featureGroup();
    mymap.addLayer(this.markersLayer);
    for (const l of latlngs) {
        const marker = L.marker([l[0], l[1]]);
        marker.setIcon(icon)
        marker.addTo(markersLayer);
	}
	
    for (const c of cots_points) {
        const marker = L.marker([c[0], c[1]]);
        marker.setIcon(red_square)
        marker.addTo(markersLayer);
        marker.bindPopup(makePopup(c[2]))
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



def map_html_str(_track, cots_waypoints):
    # try:
    #     make_photo_csv(folder)
    # except Exception as e:
    #     pass
    try:
        logger.info(len(_track))

        if _track is None or len(_track) < 2:
            return "<html>No Map</html"

        track_str = str(_track)
        html = html_str.replace("___PASTE_TRACK_HERE___", track_str)
        html = html.replace("___PASTE_COTS_HERE___", str(cots_waypoints))

        # print(html)

        return html
    except Exception as e:
        raise UserWarning(e)

