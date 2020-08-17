import os
import ee
import time
import sys
sys.path.append("..") # Adds higher directory to python modules path
from utils import utils
from scripts import gdrive

#initialize earth engine
ee.Initialize()

#Message
TASK_COMPLETED = "The task {0} launched on your GEE account is now completed"
ALREADY_COMPLETED = "The task {0} has already been completed on your GEE account"

def download_to_disk(filename, image, aoi_name):
    """download the tile to the GEE disk
    
    Args:
        filename (str): descripsion of the file
        image (ee.FeatureCollection): image to export
        aoi_name (str): Id of the aoi used to clip the image
        
    Returns:
        task (ee.Task) : the launched task
    """
    task_config = {
        'image':image,
        'description':filename,
        'scale': 30,
        'region':ee.FeatureCollection(aoi_name).geometry(),
        'maxPixels': 1e13
    }
    
    task = ee.batch.Export.image.toDrive(**task_config)
    task.start()
    
    return task

def get_alerts(aoi_name, year):
    """ get the alerts from the GLAD project
    
    Args:
        aoi_name (str): Id of the Aoi to retreive the alerts
        year (str): year on str format as YYYY
        
    Returns:
        alerts (ee.FeatureCollection): the Glad alert clipped on the AOI
    """
    
    aoi = ee.FeatureCollection(aoi_name)
    all_alerts  = ee.ImageCollection('projects/glad/alert/UpdResult')
    
    #since the bug of august 2020 I need to remove the images that doesn't contain the 9 bands 
    def numbands(image):
        return ee.Algorithms.If(image.bandNames().length().eq(9),image)
    if year == '2019':
        all_alerts = all_alerts.map(numbands,True)
    
    alerts = all_alerts.select('conf' + year[-2:]).mosaic().clip(aoi);
    
    return alerts
    
def gee_process(asset_name, year, widget_alert):
    
    global widget_gee_process_alert
    
    
    #search for the task in task_list
    filename = utils.construct_filename(asset_name, year)
    current_task = utils.search_task(filename)
    
    #search for the files in gdrive
    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)
    
    #launch the task in GEE 
    if current_task == None or files == []:
        
        alerts = get_alerts(asset_name, year)
        current_task = download_to_disk(filename, alerts, asset_name)
        utils.wait_for_completion(filename, widget_alert)
        
        utils.displayIO(widget_alert, 'success', TASK_COMPLETED.format(filename))            
    
    elif current_task.state != 'COMPLETED':
        utils.wait_for_completion(filename, widget_alert)
        utils.displayIO(widget_alert, 'success', TASK_COMPLETED.format(filename)) 
    else:
        utils.displayIO(widget_alert, 'success', ALREADY_COMPLETED.format(filename))
        
    