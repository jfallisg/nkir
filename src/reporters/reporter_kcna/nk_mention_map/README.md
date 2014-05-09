# Korean Central News Agency foreign country references over time

## Requirements:

See Mike Bostocks' "Let's Make a Map" D3.js tutorial [here](http://bost.ocks.org/mike/map/).

1. Geospatial Data Abstraction Library GDAL (which includes the OGR Simple Features Library and the ogr2ogr binary that can modify Natural Earth shapefiles).
2. TopoJSON (which in turn requires Node.js)
3. (Optional) QGIS for manual shapefile attribute table viewing/editing

***

## Process to make this map

1. Download and unzip "1:110m Cultural Vector" for "Admin 0 - Countries" from [Natural Earth](http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip).
2. From the unzipped directory "ne_110m_admin_0_countries" run `ogr2ogr -f GeoJSON countries.json ne_110m_admin_0_countries.shp`.
3. Create a TopoJSON version of our country data, preserving only the "adm0_a3" feature from the original shapefiles' attributes.  This is the ISO three-character name of the country that we can use to link to our article data. `topojson -p adm0_a3 -o topo_countries.json countries.json`.
4. 