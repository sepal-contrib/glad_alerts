import csv
import ee
import os
from datetime import datetime
import time
import ipyvuetify as v
import glob
from pathlib import Path
import geemap

#initialize earth engine
ee.Initialize()

#messages 
STATUS = "Status : {0}"

def create_FIPS_dic():
    """create the list of the country code in the FIPS norm using the CSV file provided in utils
        
    Returns:
        fips_dic (dic): the country FIPS_codes labelled with english country names
    """
     
    pathname = os.path.join(os.path.dirname(__file__), 'FIPS_code_to_country.csv')
    fips_dic = {}
    with open(pathname, newline='') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            fips_dic[row[1]] = row[3]
            
        fips_sorted = {}
        for key in sorted(fips_dic):
            fips_sorted[key] = fips_dic[key]
        
    return fips_sorted

def toggleLoading(btn):
    """Toggle the loading state for a given btn in the ipyvutify lib
    
    Args:
        btn (v.Btn) : the btn to toggle
    """
    
    btn.loading = not btn.loading
    btn.disabled = btn.loading
    
def displayIO(widget_alert, alert_type, message):
    """ Display the message in a vuetify alert DOM object with specific coloring
    Args: 
        widget_alert (v.Alert) : the vuetify alert to modify
        alert_type (str) : the change the alert color
        message (v.Children) : a DOM element or a string to fill the message 
    """
    
    list_color = ['info', 'success', 'warning', 'error']
    if not alert_type in list_color:
        alert_type = 'info'
        
    widget_alert.type = alert_type
     
    current_time = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
    widget_alert.children = [
        v.Html(tag='p', children=['[{0}]'.format(current_time)]),
        v.Html(tag='p', children=[message])
   ]
    
def wait_for_completion(task_descripsion, widget_alert):
    """Wait until the selected process are finished. Display some output information

    Args:
        task_descripsion ([str]) : name of the running tasks
        widget_alert (v.Alert) : alert to display the output messages
    
    Returns: state (str) : final state
    """
    state = 'UNSUBMITTED'
    while not (state == 'COMPLETED' or state =='FAILED'):
        displayIO(widget_alert, 'info', STATUS.format(state))
        time.sleep(5)
                    
        #search for the task in task_list
        for task in task_descripsion:
            current_task = search_task(task)
            state = current_task.state
            if state == 'RUNNING': break
    
    return state

def get_aoi_name(asset_name):
    """Return the corresponding aoi_name from an assetId"""
    return os.path.split(asset_name)[1].replace('aoi_','')

def construct_filename(asset_name, date_range):
    """return the filename associated with the current task
    
    Args:
        asset_name (str): the ID of the asset
        date_range ([str, str]): the range of date to retreive the GLAD alerts (Y-m-d)
    
    Returns:
        filename (str): the filename to save the Tif files
    """
    aoi_name = get_aoi_name(asset_name)
    filename = aoi_name + '_{0}_{1}_alerts'.format(date_range[0], date_range[1]) 
    
    return filename

def search_task(task_descripsion):
    """Search for the described task in the user Task list return None if nothing is find
    
    Args: 
        task_descripsion (str): the task descripsion
    
    Returns
        task (ee.Task) : return the found task else None
    """
    
    tasks_list = ee.batch.Task.list()
    current_task = None
    for task in tasks_list:
        if task.config['description'] == task_descripsion:
            current_task = task
            break
            
    return current_task

def create_result_folder(aoiId):
    """Create a folder to download the glad images
   
    Args:
        aoiId(str) : the Id to the asset
    
    Returns:
        glad_dir (str): pathname to the glad_result folder
    """
    aoi = get_aoi_name(aoiId)
    glad_dir = os.path.join(os.path.expanduser('~'), 'glad_results') + '/'
        
    pathname = glad_dir + aoi + '/'
    if not os.path.exists(pathname):
        os.makedirs(pathname)
    
    return pathname

def create_download_link(pathname):
    result_path = os.path.expanduser(pathname)
    home_path = os.path.expanduser('~')
    download_path='/'+os.path.relpath(result_path,home_path)
    
    link = "/api/files/download?path={}".format(download_path)
    
    return link

def check_for_file(filename):
    """return the file corresponding to the pathname else False
    
    Args:
        filename (str): expected pathname of the file
      
    Returns:
        (str) : the pathname if found else False
    """
    return glob.glob(filename)

def get_shp_files():
    """return all the .shp files available in the user directories. Will verify if the .dbf and .shx exists and are located at the same place
    
    Returns: 
        shp_list (str[]): the path to every .shp complete and available, empty list if none
    """
    
    root_dir = os.path.expanduser('~')
    raw_list = glob.glob(root_dir + "/**/*.shp", recursive=True)
    
    #check if the file is complete
    shp_list = []
    for pathname in raw_list:
        path = Path(pathname)
        if os.path.isfile(path.with_suffix('.dbf')) and os.path.isfile(path.with_suffix('.shx')):
            shp_list.append(pathname)

    return shp_list 

#def get_filename(pathname):
#    """return the shp filename without it's extention and path"""
#    return Path(pathname).stem

def complete_dict(first_dict, second_dict):
    """complete the first dict with the missing keys from the second dict. thos keys values are set to 0. return a sorted dict
    """
    for key in second_dict:
            if not key in first_dict.keys():
                first_dict[key] = 0 
            
    sorted_dict = {}
    for key in sorted(first_dict):
        sorted_dict[key] = first_dict[key]
                        
    return sorted_dict

def init_result_map():
    """initialize a geemap to display the aggregated data"""
    
    #init a map center in 0,0
    m = geemap.Map(
        center=(0, 0),
        zoom=2
    )
    
    #remove layers and controls
    m.clear_layers()
    m.clear_controls()
    
    #use the carto basemap
    m.add_basemap('Esri.WorldImagery')
    
    #add the useful controls 
    m.add_control(geemap.ZoomControl(position='topright'))
    m.add_control(geemap.LayersControl(position='topright'))
    m.add_control(geemap.AttributionControl(position='bottomleft'))
    m.add_control(geemap.ScaleControl(position='bottomleft', imperial=False))

    return m
           

    
      