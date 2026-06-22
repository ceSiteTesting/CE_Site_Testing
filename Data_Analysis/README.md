# Please Read Before Using
## CE_Analysis_Code

This is the main code for analyzing the field data. Everything for the magnetometer and seismometer analysis is contained in this code. There is a .py version, which will run on any system that can run python. As well as a .ipynb, if you are using jupyter notebook. This code is capable of plotting time series, spectra, and spectrograms. You are able to select between these functions and their variables with numbered inputs. You can change variables to increase fidelity and/or plot limits.

## CE_analysis_gui

This is a GUI version of the analysis code. It has various mains and windows to plot the time series, spectra, and spectrams. You can also easily select functions and change variables.

## CE_Analaysis_Streak

This is a stripped down version of the main analysis code. It only has the ability to plot a spectral diagrams, and you will have to go into the code to change variables. However, it is much quicker to use and recommended to use this in the field.

------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------

Additionally, there are LIGO data files. These are so you can compare the field data to what is recorded at ligo. You will need to put these data files in the same directory as the code(s). The code should run with and without the data files downloaded.

------------------------------------------------------------------------------------------------------

In order for the code to operate properly, you'll need to install a package. To this in Jupyter, you'll need to go into the Qt Console; the built in terminal for anaconda navigator. There you can install the package via the method below.
```
conda install conda-forge::obspy
```
If that doesn't work, then you may need to use **pip install**
```
pip install obspy
```
After downloading the packages, you'll need to go to **Environments** and check that the packages are installed. If they are not appearing, you will need to select **Update Index**. You will then need to select the package and install it; this may take a bit. If any other packages are missing you can install them via the same method. Once everything is installed the codes should run properly.

This packages is how python converts the mseed files from the Minimus to CSV's.

Since the codes were written in Python 3.9.25, you may also need to create a new Python environment to run the codes. Additionally, you may need to download certain versions of packages.

```
conda install matplotlib=3.5.2
conda install numpy=1.21.5
conda install obspy=1.4.2
conda install pandas=1.4.4
conda install scipy=1.9.1
```

------------------------------------------------------------------------------------------------------

### CE_Analysis_Code: File Section

As stated prior, the code incorperates both the magnetometer and the seismometer analysis methods. When you first start the code you will be greeted with this menu:
```
-----------------------------------------------
What Sensor Data Would You Like to Analysis?
        
1: Magentometer
2: Seismometer
x: Exit
        
*Exit for all menu's is 'x' or enter
-----------------------------------------------

Enter your choice (1-2, x)
```

This will let the code know which defaults values and analytical methods to use. If you select Seismometer, then you have an additional menu. This is because the mseed files from the Minimus only contain one direction. So, in order to get a proper plot, you'll need three files.

```
-----------------------------------------------
            === Seismometer Menu ===
                           
        1: WebDAQ Analysis  (csv)  (Default)
        2: Minimus Analysis (mseed)
        x: Return to sensor menu
                
-----------------------------------------------
```

After you've select your desired analytical method, a pop-up will appear. This pop-up will allow you to select the file(s) you which to analysis.

----------------------------------------------

### Code Functions
After the file(s) is selected, you will see this menu:

```
-----------------------------------------------
        === Sensor Analysis Menu ===
                       
         1: Plot Time Series
         2: Plot FFT Spectrum
         3: Plot Spectrogram
         x: Return to sensor menu
                       
-----------------------------------------------
```
This is where you can analyze the field data. Each of the functions has additions menus that allow you to refine the data's fidelity.

If there is any further confusion, this is a video going through the data acquisition process as well as using the code.
https://www.youtube.com/watch?v=Re8FvCaCeBg

