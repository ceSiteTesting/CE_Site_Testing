------------------------------------------------------------------------------------------------------
## Site Evaluation API

### Libraries

This is an API for Cosmic Explorer site evaluation, developed for ArcGIS in Python. 

You will have to install the following libraries before running the code. 
- arcgis
- geopandas
- shapely
- gdal
- pyproj
- pykml

Paste the following codeblock in your terminal to install them:
```
pip install arcgis arcgis-mapping geopandas shapely pyproj pykml
```
```
conda install -c conda-forge gdal
```

### Usage

Start with the file titled "setting_up." There are two ways of logging into your ArcGIS Online account, and the comments in "setting_up" will walk you through it. The code in "setting_up" will convert the KML files of the Cosmic Explorer sites to hosted feature layers, and publish them to your ArcGIS Online web map. KMLs must be converted to feature layers for ArcGIS to run any spatial analysis on them.

The file titled "buildings_and_kml_filter" will identify, count, and extract the coordinates of all the buildings within a certain distance of the two x- and y-arms that compose a site. The output will include two csv files, one with just the building counts for each site within a KML file, and another with both counts and coordinates for all the buildings near a site. Then, the code will filter the original KMLs down to include only those sites that have zero buildings nearby, after which it will output another csv of the number of total sites and sites with zero buildings for each KML.

The file titled "mapping_transportation" will output a csv with the kilometers of transportation lines within a certain radius of the three end stations (the x-end, y-end, and corner station) of each site. The transportation lines of interest to us include gravel roads, federal highways, and rail tracks. You will need to define the URL to the transportation lines dataset that you want the code to map. The [Transportation](https://www.arcgis.com/home/item.html?id=f42ecc08a3634182b8678514af35fac3) dataset provided by Esri is perfect for this purpose. Be aware, however, that you need to retrieve the URL of the line layer within the dataset. Scroll down on the page, and within the "Layers" section, click on, for example, the [local roads](https://www.arcgis.com/home/item.html?id=f42ecc08a3634182b8678514af35fac3&sublayer=8) line layer. The [URL](https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Transportation_v1/FeatureServer/8) can be copied from the strip on the right. I used "mapping_transportation" as a second stage of site evaluation, running it only on the KMLs with zero-building sites. If you intend to do that, head back to "setting_up" and publish your zero-building KMLs as layers first.

You will see that my code often generates "buffers" and publishes them to your web map. Essentially, the buffer you define will be the area of interest within which all your buildings and road data will be collected. 

Some things to note when running the code: 
- You will need to define file paths. Places where file paths need to be defined are clearly delineated with a comment in the code.
- When running spatial analysis on content available on your ArcGIS Online account, the code first essentially "searches" for content on your account. To find layers that you want to buffer, you can filter by title, tags, or feature type. This is why appropriate, distinct naming and tagging is so important in generating content for your account. The more content you publish, the more you want to make sure that names are distinguishable between, say, buffers for road mapping and and buffers for building extraction. For example, when running my code to map roads on zero-building sites, I look for the buffers I am interested in as follows:
```
circles = gis.content.search(
    f"title: 10km, zero, Idaho, Buffer AND owner:{gis.properties.user.username}",
    item_type="Feature Layer",
    max_items=10000
)
```
- If you have problems, feel free to shoot me an email! I would be happy to help. If you're using this code, you should know my name and you should be able to find my email address.

