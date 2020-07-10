import csv
import ee
import os
from datetime import datetime
import time
import ipyvuetify as v
import glob

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
    """Wait until the selected process is finished. Display some output information

    Args:
        task_descripsion (str) : name of the running task
        widget_alert (v.Alert) : alert to display the output messages
    """
    state = 'UNSUBMITTED'
    while state != 'COMPLETED':
        displayIO(widget_alert, 'info', STATUS.format(state))
        time.sleep(5)
                    
        #search for the task in task_list
        current_task = search_task(task_descripsion)
        state = current_task.state

def get_aoi_name(asset_name):
    """Return the corresponding aoi_name from an assetId"""
    return os.path.split(asset_name)[1].replace('aoi_','')

def construct_filename(asset_name, year):
    """return the filename associated with the current task
    
    Args:
        asset_name (str): the ID of the asset
        year (str): the year to retreive the GLAD alert
    
    Returns:
        filename (str): the filename to save the Tif files
    """
    aoi_name = get_aoi_name(asset_name)
    filename = aoi_name + '_' + str(year) + '_alerts' 
    
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
      