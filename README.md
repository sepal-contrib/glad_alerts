# glad_alerts

this module is a 3 steps process that retreive and compute the GLAD alerts ( [Hansen et al. (2016) Humid tropical forest disturbance alerts using Landsat data. Environmental Research Letters 11 034008](https://iopscience.iop.org/article/10.1088/1748-9326/11/3/034008) ) on a selected country or province.

## Step 1: Select the inputs 
- [x] select a country from the LSIB_SIMPLE 2017 list 
- [x] select a year
- [x] A map will be showing the selected country 

## Step 2: PROCESS the Alerts in GEE
- [x] verify that the inputs are declared
- [x] perform several verifications
- [x] the downloading on your Gdrive should start or you'll be notify that the process is running/completed

## Step 3: PostPRocess the alerts on SEPAL
- [x] import these files to your sepal local folder
- [ ] delete the files from my GDrive folder ? 
- [x] execute the merging command
- [ ] delete the files used for the merging command
- [x] execute the clump command 
- [x] execute the calc command
- [x] display the graph of the resulted file
