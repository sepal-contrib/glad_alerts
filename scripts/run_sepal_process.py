import time
import subprocess
import glob
import os
import ee
import sys
sys.path.append("..") # Adds higher directory to python modules path
from utils import utils
from scripts import gdrive
from threading import Thread
import ipyvuetify as v
import getpass

#initialize earth engine
ee.Initialize()

#Message
START_SEPAL = "the process has been launch on your SEPAL account"
NO_TASK = "The GEE process has not been completed, launch it or run a status check through step 2."
ALREADY_DONE = "This computation has already been performed\nYou can find your results in the glad_result folder of your computer"
COMPUTAION_COMPLETED = "Computation complete"

#function 
def merge(filename, alert_map, glad_dir, output_debug):
    """ merge into a single tif files
    
    Args:
        filename (str): filename pattern of the Tif to merge
        alert_map (str): output filename
        glad_dir (tr): glad result folder
        
    Returns:
        process.stdout (str): output of the process
    """
    
    #create command
    command = [
        'gdal_merge.py',
        '-o', alert_map,
        '-v', '-co', '"COMPRESS=LZW"'
    ]
    #add the input files
    for file in glob.glob(glad_dir + filename):
        command.append(file)

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    ) 
    
    output_debug.append(v.Html(tag='p', children=['merge output: {}'.format(process.stdout)]))
    
    return process.stdout
    
def clump(alert_map, clump_map, output_debug):
    """ clump the results
    
    Args:
        alert_map (str): pathname to the alert tif file
        clump_map (str): pathname to the tmp clump file
    
    Returns:
        process.stdout (str): output of the process
    """
    
    process = subprocess.run(
        [
            'oft-clump', 
            '-i', alert_map, 
            '-o', clump_map
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    output_debug.append(v.Html(tag='p', children=['clump output: {}'.format(process.stdout)]))
    return process.stdout
    
def calc(cwd, clump_map, alert_map, alert_stats, output_debug):
    """Compute the statistics per each individual clump
    
    Args:
        clump_map (str): pathname to the clump tif file
        alert_map (str): pathname to the alerts tif file
        alert_stat (str): pathname to the output path
        
    Results:
        process.stdout (str): output of the process
    """
    process = subprocess.run(
        [
            'oft-his', 
            '-um', clump_map, 
            '-i', alert_map, 
            '-o', alert_stats,
            '-maxval','3'
        
        ],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    output_debug.append(v.Html(tag='p', children=['hist output: {}'.format(process.stdout)]))
    return(process.stdout)  


def download_task_tif(filename, glad_dir):
    """Download the tif files from your google drive folder to the local glad_results folder
    
    Args:
        filename (str): pathname pattern to the .tif files
        glad_dir (str): pathname to the local gad_result directory
    """
    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)
    drive_handler.download_files(files, glad_dir)
    
def delete_local_file(pathname):
    """delete the files that have been already merged
    
    Args:
        pathnamec (str): the pathname patern to the .tif files 
        
    Returns: 
        (str): a message corresponding to the number of deleted files
    """
    #list the input files
    file_list = []
    for file in glob.glob(pathname):
        file_list.append(file)
        
    count = 0
    for file in file_list:
        os.remove(file)
        count += 1
        
    return "{0} files deleted".format(count)


def run_sepal_process(asset_name, year, widget_alert):
    """execute the 3 different operations of the computation successively: merg, clump and compute
    
    Args:
        asset_name (str): the assetId of the aoi computed in step 1
        year (str): the year used to compute the glad alerts
        widget_alert (v.Alert) the alert that display the output of the process
        
    Returns:
        (str,str): the links to the .tif (res. .txt) file 
    """
    
    aoi_name= utils.get_aoi_name(asset_name)
        
    #define the files variables
    glad_dir = utils.create_result_folder(asset_name)
    
    #year and country_code are defined by step 1 cell
    alert_map   = glad_dir + aoi_name + '_' + year + '_glad.tif'
    clump_map   = glad_dir + aoi_name + '_' + year + '_tmp_clump_.tif'
    alert_stats = glad_dir + aoi_name + '_' + year + '_stats.txt'
    cwd = os.path.join(os.path.expanduser('~'), 'tmp')
        
    filename = utils.construct_filename(asset_name, year)
    #check that the Gee process is finished
    if not utils.search_task(filename):
        utils.displayIO(widget_alert, 'error', NO_TASK)
        return ('#', '#')
        
    #check that the process is not already done
    if utils.check_for_file(alert_stats):
        utils.displayIO(widget_alert, 'success', ALREADY_DONE)
        return (utils.create_download_link(alert_map), utils.create_download_link(alert_stats))
    
    #download from GEE
    download_task_tif(filename, glad_dir)
        
    #process data with otf
    output_debug = []
    pathname = utils.construct_filename(asset_name, year) + "*.tif"
     
    output_debug.append(v.Html(tag='p', children=["pathname:{}".format(pathname)]))
    output_debug.append(v.Html(tag='p', children=["alert_map:{}".format(alert_map)]))
    output_debug.append(v.Html(tag='p', children=["glad_dir:{}".format(glad_dir)]))
    
    t_merge = Thread(target=merge, args=(pathname, alert_map, glad_dir, output_debug))
    utils.displayIO(widget_alert, 'info', 'starting merging')
    time.sleep(2)
    t_merge.start()
    while t_merge.is_alive():
        utils.displayIO(widget_alert, 'info', 'status: MERGE RUNNING')
    utils.displayIO(widget_alert, 'info', 'status: MERGE COMPLETED')
        
    time.sleep(2)
            
    io = delete_local_file(glad_dir + pathname)
    utils.displayIO(widget_alert, 'info', io)
        
    time.sleep(2)
    
    output_debug.append(v.Html(tag='p', children=["alert_map:{}".format(alert_map)]))
    output_debug.append(v.Html(tag='p', children=["clump_map:{}".format(clump_map)]))
            
    t_clump = Thread(target=clump, args=(alert_map, clump_map, output_debug))
    utils.displayIO(widget_alert, 'info', 'starting clumping')
    time.sleep(2)
    t_clump.start()
    while t_clump.is_alive():
        utils.displayIO(widget_alert, 'info', 'status: CLUMPING RUNNING')
    utils.displayIO(widget_alert, 'info', 'status: CLUMPING COMPLETED')
        
    time.sleep(2)
            
    output_debug.append(v.Html(tag='p', children=["alert_stats:{}".format(alert_stats)]))
    
    t_calc = Thread(target=calc, args=(cwd, clump_map, alert_map, alert_stats, output_debug))
    utils.displayIO(widget_alert, 'info', 'starting computation')
    time.sleep(2)
    t_calc.start()
    while t_calc.is_alive():
        utils.displayIO(widget_alert, 'info', 'status: COMPUTATION RUNNING')
    utils.displayIO(widget_alert, 'info', 'status: COMPUTATION COMPLETED')
        
    time.sleep(2)
    
    #io = delete_local_file(clump_map)
    #utils.displayIO(widget_alert, 'info', io)
    
    time.sleep(2)
    
    utils.displayIO(widget_alert, 'success', COMPUTAION_COMPLETED)
    
    output_debug.append(v.Html(tag='p', children=["env: {}".format(os.environ)]))
    
    output_debug.append(v.Html(tag='p', children=["user: {}".format(getpass.getuser())]))

    
    widget_alert.children = output_debug
    
    
    return (utils.create_download_link(alert_map), utils.create_download_link(alert_stats))
    
