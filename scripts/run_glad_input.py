import ee
import time
import sys
import re
sys.path.append("..") # Adds higher directory to python modules path
from utils import utils

#initialize earth engine
ee.Initialize()

#messages to display
NO_SELECTION = 'No selection method have bee picked up'
NO_COUNTRY = 'No Country have been selected'
ASSET_ALREADY_EXIST = "The asset was already existing you can continue to use it. It's also available at :{0}"
ASSET_CREATED = "The asset has been created under the name : {0}"
NAME_USED = "The name was already in used, change it or delete the previous asset in your GEE acount"
NO_ASSET = "No Asset have been provided"
CHECK_IF_ASSET = "Check carefully that your string is an assetId"
NOT_AVAILABLE = "This function is not yet available"
NO_SHAPE = "No shape have been drawn on the map"


def isAsset(asset_descripsion, folder):
    """Check if the asset already exist in the user asset folder
    
    Args: 
        asset_descripsion (str) : the descripsion of the asset
        folder (str): the folder of the glad assets
        
    Returns:
        exist (bool): true if already in folder
    """
    exist = False
    liste = ee.data.listAssets({'parent': folder})['assets']
    for asset in liste:
        if asset['name'] == folder + asset_descripsion:
            exist = True
            break
    return exist    

def run_GLAD_input(file_input, file_name, country_selection, asset_name, drawing_method, widget_alert, list_method, m, drawn_feat):
    """ compute the AOI for the step 1 of the GLAD alert module

    Args:
        file_input (str): the file to retreive from the user folder. It must be a .shp file
        file_name (str): name of the aoi that will be used troughout the process
        country_selection (str): a country name in english (starting with a capital letter)
        asset_name (str): the assetId of a existing asset
        drawing_method (str): the name of the method selected to create the asset
        widget_alert (v.Alert): the widget used to display the process informations
        list_method ([str]): list of the method use to select an AOI
        m (geemap.Map) : the map to draw the shape
        drawn_feat (ee.FeatureCollection): the last drawn object on the map
        
    Returns:
        asset (str) : the AssetId of the AOI
    """
    #go to the glad folder in gee assets 
    folder = ee.data.getAssetRoots()[0]['id'] + '/'
    
    #check the drawing method
    if drawing_method == None: #not selected
        
        utils.displayIO(widget_alert, 'warning', NO_SELECTION)    
        asset = None
        
    elif drawing_method == list_method[0]: #use a country boundary
        
        if country_selection == None:
            utils.displayIO(widget_alert, 'warning', NO_COUNTRY) 
            asset = None
            return asset
        country_code = utils.create_FIPS_dic()[country_selection] 
        asset_descripsion = 'Glad_{0}'.format(country_code) 
        asset = folder + asset_descripsion
            
        #check asset existence
        if isAsset(asset_descripsion, folder):
            utils.displayIO(widget_alert, 'info', ASSET_ALREADY_EXIST.format(asset))
            return asset
        
        country = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_co', country_code))
                
        #create and launch the task
        task_config = {
            'collection': country, 
            'description':asset_descripsion,
            'assetId': asset
        }
        task = ee.batch.Export.table.toAsset(**task_config)
        task.start()
        utils.wait_for_completion(asset_descripsion, widget_alert)
          
        utils.displayIO(widget_alert, 'success',ASSET_CREATED.format(asset))
                
    elif drawing_method == list_method[1]: #draw a shape
             
        aoi = drawn_feat 
        asset_name = "Glad_{0}".format(file_name.replace(' ', '_'))
        
        #check if something is drawn 
        if drawn_feat == None:
            asset = None
            utils.displayIO(widget_alert, 'error', NO_SHAPE)
            return asset
              
        #check asset existence
        if isAsset(asset_name, folder):
            asset = None
            utils.displayIO(widget_alert, 'error', NAME_USED)
            return asset 
        
        asset_name = re.sub('[^a-zA-Z\d]', '_', asset_name)
        asset = folder + asset_name
            
        #create and launch the task
        task_config = {
            'collection': aoi, 
            'description':asset_name,
            'assetId': asset
        }
        task = ee.batch.Export.table.toAsset(**task_config)
        task.start()
        utils.wait_for_completion(asset_name, widget_alert)
           
        utils.displayIO(widget_alert, 'success',ASSET_CREATED.format(asset))           
            
    elif drawing_method == list_method[3]: #use GEE asset
        
        #verify that there is an asset
        if asset_name == '' or asset_name == None:
            asset = None
            utils.displayIO(widget_alert, 'error', NO_ASSET) 
        else:
            asset = asset_name
            utils.displayIO(widget_alert, 'info', CHECK_IF_ASSET)
            
    elif drawing_method == list_method[2]: #upload file
        
        ee_object = geemap.shp_to_ee(file_input)
        asset_name = "Glad_" + re.sub('[^a-zA-Z\d]','_',file_name)
        
        #check asset's name
        if isAsset(asset_name, folder):
            asset = None
            utils.displayIO(widget_alert, 'error', NAME_USED)
        else:
            asset = folder + asset_name
            
            #launch the task
            task_config = {
                'collection': ee_object, 
                'description':asset_name,
                'assetId': asset
            }
            task = ee.batch.Export.table.toAsset(**task_config)
            task.start()
            utils.wait_for_completion(asset_name, widget_alert)
                   
            utils.displayIO(widget_alert, 'success',ASSET_CREATED.format(asset))
            
        #currently not usable so undo everything
        asset = None
        utils.displayIO(widget_alert, 'error',NOT_AVAILABLE)
            
    return asset