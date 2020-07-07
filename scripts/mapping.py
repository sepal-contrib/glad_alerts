import geemap
import ee 

#initialize earth engine
ee.Initialize()

def init_map():
    '''Initialize a map centered on the point [0,0] with zoom at 1
    
    Returns:
        dc (DrawControl): a draw control for polygon drawing 
        m (Map): a map
    '''
    center = [0, 0]
    zoom = 2

    dc = geemap.DrawControl(
        marker={},
        circlemarker={},
        polyline={},
        rectangle={'shapeOptions': {'color': '#0000FF'}},
        circle={'shapeOptions': {'color': '#0000FF'}},
        polygon={'shapeOptions': {'color': '#0000FF'}},
     )

    m = geemap.Map(center=center, zoom=zoom)
    m.clear_layers()
    m.clear_controls()
    m.add_basemap('Esri.WorldImagery')
    m.add_basemap('CartoDB.Positron')
    m.add_control(geemap.ZoomControl(position='topright'))
    m.add_control(geemap.LayersControl(position='topright'))
    m.add_control(geemap.ScaleControl(position='bottomleft', imperial=False))
    
    return (dc, m)

def update_map(m, dc, asset_name):
    """Update the map with the asset overlay and by removing the selected drawing controls
    
    Args:
        m (Map): a map
        dc (DrawControl): the drawcontrol to be removed
        asset_name (str): the asset ID in gee assets
    """
    m.centerObject(ee.FeatureCollection(asset_name), zoom=4)
    m.addLayer(ee.FeatureCollection(asset_name), {'color': 'green'}, name='aoi')
    dc.clear()
    m.remove_control(dc)
    
            
    