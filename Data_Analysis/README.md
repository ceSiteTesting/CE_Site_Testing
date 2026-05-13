# Read Me
## Data Analysis Code

This is the analysis code for the data retrieved when conducting CE site testing. Everything for the magnetometer and seismometer analysis is contained in this is code. There is a .py version, which will run on any system that can run python. As well as a .ipynb, if you are using jupyter notebook. The code operates via a GUI and user inputs. This way the user does not have to maunally go into the code and change variables.

Additionally, there are LIGO data files. These are so you can compare the field data to what is recorded at ligo. You will need to put these data files in the same directory as the code(s). The code should run with and without the data files downloaded.

In order for the code to operate properly, you'll need to install a package. To this in Jupyter, you'll need to go into the Qt Console; the built in terminal for anaconda navigator. There you can install the package via the method below.
```
conda install conda-forge::obspy
```
If that doesn't work, then you may need to use **pip install**
```
pip install obspy
```
After downloading the packages, you'll need to go to **Environments** and check that the packages are installed. If they are not appearing, you will need to select **Update Index**. You will then need to select the package and install it; this may take a bit. If any other packages are missing you can install them via the same method. Once everything is installed the codes should run properly

### FIle Section
As stated prior, the code incorperates both the magnetometer and the seismometer analysis methods. When you first start the code you will be see these:
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
This will let the code know which defaults values and methods to use. Since, the data acquisition/analysis is slighty different between the mag and seis.

Once you've selected magnetometer or seismometer, you will be greeted with a GUI. If you are using Windows, the icon will appear in your task bar. The icon will be the same as a file document with the top right corner folded. Once you click on that, it will bring up the GUI for fill selection. After you've found your desired file, you will need to close the GUI window in order to proceed in the code.

### Code Functions
The code has three primary plotting functions.
- Time series
- Amplitude Spectral Density Plot (ASD Plot)
- Spectrogram

There is a menu to go in between these functions. As well as additional menus to change the parameters of each plot and to further the data analysis process. Each function/option is denoted by a number. So, you simply need to type in the number an hit enter. 

If you have any questions or confusion, this is a video going through the data acquisition process as well as using the code.
https://www.youtube.com/watch?v=Re8FvCaCeBg

