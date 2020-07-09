import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bqplot import *
import sys
sys.path.append("..") # Adds higher directory to python modules path
from utils import utils
import csv

def display_results(asset_name, year):
    
    glad_dir = utils.create_result_folder()
    aoi_name = utils.get_aoi_name(asset_name) 
    alert_stats = glad_dir + "stats_glad_" + year + "_" + aoi_name + ".txt"
    
    data = np.loadtxt(alert_stats, delimiter=' ')
    
    alert_csv = create_csv(data, aoi_name, glad_dir, year)
    
    bins=30

    #need to confirm who's who
    Y_conf = data[:,5]
    Y_conf = np.ma.masked_equal(Y_conf,0).compressed()
    maxY5 = np.amax(Y_conf)

    #null if all the alerts have been confirmed
    Y_prob = data[:,4]
    Y_prob = np.ma.masked_equal(Y_prob,0).compressed()
    try:
        maxY4 = np.amax(Y_prob)
        data_hist = [Y_conf, Y_prob]
        colors = ["#C26449", "#59C266"]
        labels = ['confirmed alert', 'potential alert']
    except ValueError:  #raised if `Y_prob` is empty.
        maxY4 = 0
        data_hist = [Y_conf]
        colors = ["#C26449"]
        labels = ['confirmed alert']
        pass
    
    #plot in kilometers ?
    
    hist_y, hist_x = np.histogram(Y_conf, bins=30, weights=Y_conf)
    
    x_sc = LinearScale()
    y_sc = LinearScale()

    bar = Bars(x=hist_x, y=hist_y, scales={'x': x_sc, 'y': y_sc})
    ax_x = Axis(label='patch size (px)', scale=x_sc)
    ax_y = Axis(label='number of pixels', scale=y_sc, orientation='vertical')
    title ='Distribution of GLAD alerts for {0} in {1}'.format(aoi_name, year)
    fig_hist = Figure(
        title= title,
        marks=[bar], 
        axes=[ax_x, ax_y], 
        padding_x=0.025, 
        padding_y=0.025
    )
    
    fig_hist.layout.width = 'auto'
    fig_hist.layout.height = 'auto'
    fig_hist.layout.min_height = '300px' # so it still shows nicely in the notebook

    filepath = glad_dir + 'hist_' + aoi_name + '_' + year + '.png'
    
    if not utils.check_for_file(filepath):
        #fig_hist.save_png(filepath)
        create_png(data_hist, labels, colors, bins, max(maxY4,maxY5), title, filepath)
    
    return (fig_hist, utils.create_download_link(filepath), utils.create_download_link(alert_csv))

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
    #plt.yscale('log')
    plt.legend(loc='upper right')
    plt.title(title)
    plt.xlabel('patch size (px)')
    plt.ylabel('number of pixels')

    plt.savefig(filepath)   # save the figure to file
    
def create_csv(data, aoi_name, glad_dir, year):
    
    #need to confirm who's who
    Y_conf = data[:,5]
    Y_conf = np.ma.masked_equal(Y_conf,0).compressed()
    unique, counts = np.unique(Y_conf, return_counts=True)
    conf_dict = dict(zip(unique, counts))
    #null if all the alerts have been confirmed
    Y_prob = data[:,4]
    Y_prob = np.ma.masked_equal(Y_prob,0).compressed()
    
    
    prob = None
    if not Y_prob == []:
        unique, counts = np.unique(Y_prob, return_counts=True)
        prob_dict = dict(zip(unique, counts))
        
        #add missing keys to conf
        conf_dict = complete_dict(conf_dict, prob_dict) 
                
        #add missing keys to prob
        prob_dict = complete_dict(prob_dict, conf_dict)
                
        prob = ['potential alerts']
        for key in prob_dict:
            prob.append(prob_dict[key])
        
    
    header = ['patch size']
    conf = ['confirmed alerts']
    for key in conf_dict: 
        header.append('{:d}'.format(int(key)))
        conf.append(conf_dict[key])
    
    filename = glad_dir + 'distrib_' + aoi_name + '_' + year + '.csv'
    if utils.check_for_file(filename):
        return filename
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow(conf)
        if prob:
           writer.writerow(prob) 
    
    return filename
                        
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