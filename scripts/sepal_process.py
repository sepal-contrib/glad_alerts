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
from sepal_ui.scripts import utils as su
from sepal_ui import widgetFactory as wf
from utils import messages as ms
from scripts import gee_process
from utils import parameters as pm
from sepal_ui.scripts import mapping
import numpy as np
from bqplot import *
import matplotlib.pyplot as plt
import csv
from sepal_ui import oft 
from sepal_ui import gdal as sgdal

#initialize earth engine
ee.Initialize()


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
    
    output_debug.append(v.Html(tag='p', children=['gdal_merge output: {}'.format(process.stdout)]))
    
    return process.stdout
    
 


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


def sepal_process(asset_name, year, output, oft_output):
    """execute the 3 different operations of the computation successively: merge, clump and compute
    
    Args:
        asset_name (str): the assetId of the aoi computed in step 1
        year (str): the year used to compute the glad alerts
        widget_alert (v.Alert) the alert that display the output of the process
        
    Returns:
        (str,str): the links to the .tif (res. .txt) file 
    """
    
    output_debug = [v.Html(tag="h3", children=['Process outputs'])]
    
    aoi_name= utils.get_aoi_name(asset_name)
        
    #define the files variables
    glad_dir = utils.create_result_folder(asset_name)
    
    #year and country_code are defined by step 1 cell
    alert_map   = glad_dir + aoi_name + '_' + year + '_glad.tif'
    clump_map   = glad_dir + aoi_name + '_' + year + '_tmp_clump_.tif'
    alert_stats = glad_dir + aoi_name + '_' + year + '_stats.txt'
    cwd = os.path.expanduser('~')
    
    output_debug.append(v.Html(tag='p', children=["glad_dir: {}".format(glad_dir)]))
    output_debug.append(v.Html(tag='p', children=["alert_map: {}".format(alert_map)]))
    output_debug.append(v.Html(tag='p', children=["clump_map: {}".format(clump_map)]))
    output_debug.append(v.Html(tag='p', children=["alert_stats:{}".format(alert_stats)]))
        
    filename = utils.construct_filename(asset_name, year)
    
    #check that the tiles exist in gdrive
    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)
    
    if files == []:
        su.displayIO(output, ms.NO_TASK, 'error')
        return (None, None)
        
    #check that the process is not already done
    if utils.check_for_file(alert_stats):
        su.displayIO(output, ms.ALREADY_DONE, 'success')
        return (alert_map, alert_stats)
    
    #download from GEE
    download_task_tif(filename, glad_dir)
        
    #process data with otf
    pathname = filename + "*.tif"
    
    #create the files list 
    files = []
    for file in glob.glob(glad_dir + pathname):
        files.append(file)
    
    #run the merge process
    su.displayIO(output, ms.MERGE_TILE)
    time.sleep(2)
    io = sgdal.merge(files, out_filename=alert_map, v=True, co='"COMPRESS=LZW"', output=output)
    output_debug.append(v.Html(tag='p', children=[io]))
    
    #delete local files
    io = delete_local_file(glad_dir + pathname)
    su.displayIO(output, io)
    
    #compress raster
    
    #clump the patches together
    su.displayIO(output, ms.IDENTIFY_PATCH)
    time.sleep(2)
    io = oft.clump(alert_map, clump_map, output=output)
    output_debug.append(v.Html(tag='p', children=[io]))
    
    #compress clump raster
    
    #create the histogram of the patches
    su.displayIO(output, ms.PATCH_SIZE)
    time.sleep(2)
    io = oft.his(alert_map, alert_stats, maskfile=clump_map, maxval=3, output=output)
    output_debug.append(v.Html(tag='p', children=[io]))
    
    su.displayIO(output, ms.COMPUTAION_COMPLETED, 'success')  
    
    oft_output.children = output_debug
    
    return (alert_map, alert_stats)

def display_results(asset_name, year, raster):
    
    glad_dir = utils.create_result_folder(asset_name)
    aoi_name = utils.get_aoi_name(asset_name) 
    alert_stats = glad_dir + aoi_name + '_' + year + '_stats.txt'
    
    data = np.loadtxt(alert_stats, delimiter=' ')
    
    ####################
    ##     tif link   ##
    ####################
    tif_btn = wf.DownloadBtn(ms.TIF_BTN, raster)
    
    ####################
    ##    csv file    ##
    ####################
    
    alert_csv = create_csv(data, aoi_name, glad_dir, year)
    csv_btn = wf.DownloadBtn(ms.CSV_BTN, alert_csv)
    
    ##########################
    ##    create the figs   ##
    ##########################
    
    bins=30

    #need to confirm who's who
    Y_conf = data[:,5]
    Y_conf = np.ma.masked_equal(Y_conf,0).compressed()
    maxY5 = np.amax(Y_conf)

    #null if all the alerts have been confirmed
    Y_prob = data[:,4]
    Y_prob = np.ma.masked_equal(Y_prob,0).compressed()
    
    x_sc = LinearScale()
    y_sc = LinearScale()  
    
    ax_x = Axis(label='patch size (px)', scale=x_sc)
    ax_y = Axis(label='number of pixels', scale=y_sc, orientation='vertical')  
    
    figs = []
    
    try:
        maxY4 = np.amax(Y_prob)
        data_hist = [Y_conf, Y_prob]
        colors = pm.getPalette()
        labels = ['confirmed alert', 'potential alert']
        prob_y, prob_x = np.histogram(Y_prob, bins=30, weights=Y_prob)
        
        #cannot plot 2 bars charts with different x_data
        bar = Bars(x=prob_x, y=prob_y, scales={'x': x_sc, 'y': y_sc}, colors=[colors[1]])
        title ='Distribution of the potential GLAD alerts for {0} in {1}'.format(aoi_name, year)
    
        figs.append(Figure(
            title= title,
            marks=[bar], 
            axes=[ax_x, ax_y], 
            padding_x=0.025, 
            padding_y=0.025
        ))
    except ValueError:  #raised if `Y_prob` is empty.
        maxY4 = 0
        data_hist = [Y_conf]
        colors = [pm.getPalette()[0]]
        labels = ['confirmed alert']
        pass
    
    #cannot plot 2 bars charts with different x_data
    conf_y, conf_x = np.histogram(Y_conf, bins=30, weights=Y_conf)
    bar = Bars(x=conf_x, y=conf_y, scales={'x': x_sc, 'y': y_sc}, colors=[colors[0]])
    title ='Distribution of the confirmed GLAD alerts for {0} in {1}'.format(aoi_name, year)
    
    figs.append(Figure(
        title= title,
        marks=[bar], 
        axes=[ax_x, ax_y], 
        padding_x=0.025, 
        padding_y=0.025
    ))

    ############################
    ##       create hist      ##
    ############################
    
    png_link = glad_dir + aoi_name + '_' + year + '_hist.png'
    
    title = 'Distribution of the GLAD alerts \nfor {0} in {1}'.format(aoi_name, year)
    png_link = create_png(data_hist, labels, colors, bins, max(maxY4,maxY5), title, png_link)
    png_btn = wf.DownloadBtn(ms.PNG_BTN, png_link)
    
    ###########################
    ##      create the map   ##
    ###########################
    m = display_alerts(asset_name, year)
    
    #########################
    ##   sum-up layout     ##
    #########################
    
    #create the partial layout 
    partial_layout = v.Layout(
        Row=True,
        align_center=True,
        class_='pa-0 mt-5', 
        children=[
            v.Flex(xs12=True, md6=True, class_='pa-0', children=figs),
            v.Flex(xs12=True, md6=True, class_='pa-0', children=[m])
        ]
    )
    
    #create the display
    children = [ 
        v.Layout(Row=True, children=[
            csv_btn,
            png_btn,
            tif_btn
        ]),
        partial_layout
    ]
    
    
    return children

def create_png(data_hist, labels, colors, bins, max_, title, filepath):
    """useless function that create a matplotlib file because bqplot cannot yet export without a popup
    """
    plt.hist(
        data_hist, 
        label=labels, 
        weights=data_hist,
        color=colors, 
        bins=bins, 
        histtype='bar', 
        stacked=True
    )
    plt.xlim(0, max_)
    plt.legend(loc='upper right')
    plt.title(title)
    plt.xlabel('patch size (px)')
    plt.ylabel('number of pixels')

    plt.savefig(filepath)   # save the figure to file
    
    return filepath
    
def create_csv(data, aoi_name, glad_dir, year):
    
    Y_conf = data[:,5]
    Y_conf = np.ma.masked_equal(Y_conf,0).compressed()
    unique, counts = np.unique(Y_conf, return_counts=True)
    conf_dict = dict(zip(unique, counts))
    #null if all the alerts have been confirmed
    Y_prob = data[:,4]
    Y_prob = np.ma.masked_equal(Y_prob,0).compressed()
    unique, counts = np.unique(Y_prob, return_counts=True)
    prob_dict = dict(zip(unique, counts))
        
    #add missing keys to conf
    conf_dict = utils.complete_dict(conf_dict, prob_dict) 
                
    #add missing keys to prob
    prob_dict = utils.complete_dict(prob_dict, conf_dict)
                
    prob = ['potential alerts']
    for key in prob_dict:
        prob.append(prob_dict[key])
            
    header = ['patch size']
    conf = ['confirmed alerts']
    for key in conf_dict: 
        header.append('{:d}'.format(int(key)))
        conf.append(conf_dict[key])
    
    filename = glad_dir + aoi_name + '_' + year + '_distrib.csv'
    if utils.check_for_file(filename):
        return filename
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow(conf)
        writer.writerow(prob) 
    
    return filename

def display_alerts(aoi_name, year):
    """dipslay the selected alerts on the geemap
    currently re-computing the alerts on the fly because geemap is faster to use ee interface than reading a .tif file
    """
    
    #create the map
    m = utils.init_result_map()
    
    aoi = ee.FeatureCollection(aoi_name)
    alerts = gee_process.get_alerts(aoi_name, year)
    alertsMasked = alerts.updateMask(alerts.gt(0));
    
    palette = pm.getPalette()
    m.addLayer(alertsMasked, {
        'bands':['conf' + year[-2:]], 
        'min':2, 
        'max':3, 
        'palette': palette[::-1]
    }, 'alerts') 
    
    #Create an empty image into which to paint the features, cast to byte.
    empty = ee.Image().byte()
    outline = empty.paint(**{'featureCollection': aoi, 'color': 1, 'width': 3})
    m.addLayer(outline, {'palette': '283593'}, 'aoi')
                 
    m.centerObject(aoi, zoom=mapping.update_zoom(aoi_name))
    
    legend_keys = ['potential alerts', 'confirmed alerts']
    legend_colors = palette[::-1]
    
    m.add_legend(legend_keys=legend_keys, legend_colors=legend_colors, position='topleft')
    
    return m
                 
    
    
    
