# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_RedTideProcessing.ipynb.

# %% auto 0
__all__ = ['summed_rows', 'Xpixels', 'wavelengths', 'create_time', 'Fraunhofer_lines', 'HG_lines', 'sentinal_s2a',
           'hhmmss_to_sod', 'now_utc', 'hms2sod', 'extract_hms', 'configure_json_spectra',
           'calibrate_using_2_wavelengths', 'read_spectra', 'w_to_pixel', 'pixel_to_w', 'w_range_pixels',
           'get_list_of_json_spectra', 'json_specs_to_df', 'is_water', 'wavelength_2_RGB', 'wavelength_2_RGB_str',
           'Sentinal_Band', 'sentinel_update', 'nearest_rgb_image', 'read_gps_file_to_df', 'compute_gps_positions',
           'get_bearing', 'get_list_of_flight_lines', 'get_list_of_hab_files', 'get_fluorescence',
           'get_fluorescence_700', 'get_fluorescence_683']

# %% ../nbs/00_RedTideProcessing.ipynb 4
import glob
import numpy             as np
import pandas            as pd
import cv2               as cv
import datetime          as dt
import glob
import matplotlib.pylab  as plt
import numpy             as np
import pandas            as pd
import pandas            as pd
import time
from geographiclib.geodesic import Geodesic
from           PIL          import Image   
from       skimage          import io

# %% ../nbs/00_RedTideProcessing.ipynb 16
summed_rows = 0
Xpixels     = np.array(1)
wavelengths = np.array(1)
create_time = dt.datetime.utcnow()

# %% ../nbs/00_RedTideProcessing.ipynb 20
def hhmmss_to_sod( hhmmss, Usecs=0):
    """
    Converts a time string in 'HHMMSS' format to a seconds-of-the-day
    including an optional microseconds fraction.

    Parameters:
    ----------- 
    hhmmss : str
    Usecs  : str, default=0

    Returns: 
    --------
    float
      Seconds of the day including the fractional part computed from `Usecs`
    
    Description:
    ------------
    hhmmss where hh is hours, mm is minutes, and ss is seconds. Example '123456'
    is 12 hours, 34 minutes, and 56 seconds. A string representing the number of
    microseconds since the last second increment, ie the fractional part of a second. 
    Example: '954561' represents 0.954561 seconds, or 954,561 microseconds since the
    last seconds rollover. Returns A single floating point value of the seconds since
    midnight plus the fractional seconds.

    Examples:
    ---------
    To be added.

    """
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    fsod = hh*3600 + mm*60 + ss + float(Usecs) * 1e-6
    return fsod

# %% ../nbs/00_RedTideProcessing.ipynb 22
def now_utc( fmt='%Y-%m%d %H:%M:%S'):
    """ Return the current UTC date and time as a string.  Example return: '2021-0812 15:39:41'.
    See: http://shorturl.at/koOQ7 for timeformat options & directives.
    """
    t = dt.datetime.utcnow()
    ts = f'{t:{fmt}}'
    return ts

# %% ../nbs/00_RedTideProcessing.ipynb 24
#debug_hms2sod = False
def hms2sod( str, debug=False):
  '''
  Converts an ASCII string in the form 'HH:MM"SS' to seconds of the day. Works with
  fractional seconds.
  '''
  t_lst = str.split('.')
  ts = time.strptime( t_lst[0], '%H:%M:%S')
  if len(t_lst) > 1:
    fs = float("."+t_lst[1] )
  else:
    fs = 0.0
  sod = ts[3]*3600 + ts[4]*60 + ts[5] + fs
  return sod

# %% ../nbs/00_RedTideProcessing.ipynb 27
def extract_hms( fn):
    '''Extract the HHMMSS and Fsecs strings from filename "fn"

    Returns:
    --------
    ( hhmmss:str, fsecs:str, hhmmss.fsecs:float, sod.fsecs:float )
    '''
    lst = fn.split('-')
    sod = hhmmss_to_sod( lst[-3], Usecs=lst[-2] )
    return ( lst[-3], lst[-2], float(lst[-3])+float(lst[-2])*1e-6, sod  )

# %% ../nbs/00_RedTideProcessing.ipynb 30
def configure_json_spectra(f:str   # Json settings file.
                        ) ->str:   # Returns the Json file name.
    '''
    Configures HabSpec internal setting according to settings found within a json spectra file 'f'.

    Parameters:
    -----------
    f : str
        HabSpec json spectra full path and file name.

    Returns:
    --------
        f:str.
    '''
    global Xpixels, summed_rows, wavelengths 
    spec = pd.read_json(f)                      # get a spectra fron a json file
    y = np.array(spec['hab_spec'].spectra )     # Load the y values to an np array
    summed_rows = spec['hab_spec'].summed_rows
    Xpixels = np.arange(0,y.size )              # Construct an array of X values
    wavelengths = np.arange( y.size )
    return f

# %% ../nbs/00_RedTideProcessing.ipynb 33
def calibrate_using_2_wavelengths(
                                  pixel0:int=0,         #  pixel # for Wavelength 0
                                  wavelength0:float=0,   # Wavelength of pixel 0
                                  pixel1:int=0,         # pixel # for Wavelength 1
                                  wavelength1:float=0   # Wavelength for pixel1
                                 ):
    '''
    Generate a Numpy array of calibration wavelenghts for each pixel. configure_json_spectra(f)
    must be called beforehand inrder to set the correct number of pixels.

    Parameters:
    -----------
    pixel0 : int, default 0
    wavelength0 : float, default 0
    pixel1 : int, default 0
    wavelength1 : float, default 0

    Returns:
    --------
    Float array of calibrated wavelengths for each pixel.  The returned array is the
    same size as Xpixels.

    Example:
    ---------
    # Configure the spectra by reading a spectra file.
    fn = '/content/drive/MyDrive/Missions/2021-0717-HAB-pie/165347/hab_spectra/2021-0717-165348-272814-spec.json'
    hs.configure_json_spectra(fn)

    # Calibrate the spectra.  Pixel 73 is at 430.774nm, and pixel 941 is at 759.370nm
    hs.calibrate_using_2_wavelengths(pixel0=73, wavelength0=430.774, pixel1=941, wavelength1=759.370 )

    References:
    -----------
    The following are wavelength calibration sources.
    See: http://hyperphysics.phy-astr.gsu.edu/hbase/quantum/atspect2.html
    and: https://commons.wikimedia.org/wiki/File:Fluorescent_lighting_spectrum_peaks_labelled.gif
    and: https://en.wikipedia.org/wiki/Fluorescent_lamp#/media/File:Spectra-Philips_32T8_natural_sunshine_fluorescent_light.svg
    '''
    dp = pixel1      - pixel0              # pixel delta
    dw = wavelength1 - wavelength0         # Wavelength delta
    slope = dw/dp                          # Linear slope
    wavelengths = wavelength0 + (Xpixels-pixel0) * slope
    return wavelengths

# %% ../nbs/00_RedTideProcessing.ipynb 37
def read_spectra(f,                    # JSON Spectra file name
                   remove_bias = True, # Bol remove bias
                   y_average   = True  # Average Y values
                  ) -> float:          # Numpy array of spectral points.
    """
    Reads a Json hyperspectra file.

    Parameters:
    -----------
    f : str
      The full path name of a hyperspectra Json file.
    remove_bias : Default True
      Subtracts the minimum y value from the array of y values to remove dark current. 
      The minimum value will typically be found in the IR side and from the pixel 
      sensors that are optically obscured.
    y_average : Default True
      The Json values are the sum total of each pixel column. Each column contains 800
      pixels. Setting this to True causes the read y values to be divided by 800.

    Returns:
    --------
    Numpy array
      An array of numpy float values representing the intensity values at each pixel. 

    Description:
    ------------
    Reads a Json spectra from a file.

    Examples:
    ---------
    fn = '/content/drive/MyDrive/Missions/2021-0717-HAB-pie/165347/hab_spectra/2021-0717-165348-272814-spec.json'
    s = hs.read_spectra(fn)
    """
    spec = pd.read_json(f)
    if summed_rows == 0 :
      configure_json_spectra(f)
    y = np.array(spec['hab_spec'].spectra)

    if y_average == True:
      y = y / summed_rows

    if remove_bias == True:
      y = y - y.min()
    return y

# %% ../nbs/00_RedTideProcessing.ipynb 40
def w_to_pixel( 
  x,       #   Array of wavelengths for each pixel
  w        #   The wavelength you want the pixel number of.
) -> int:  #   The pixel
  '''
  Return the pixel index for a given wavelength `w`.  Out of range
  wavelengths cause -1 to be returned.
  '''
  dw  = (x[-1] - x[0])
  dpx = len(x)
  d  = dw/dpx
  px = int((w-x[0]) / d )
  if px < 0: 
    px = -1
  elif w > x[-1]:
    px = -1
  return px

# %% ../nbs/00_RedTideProcessing.ipynb 42
def pixel_to_w(
  x,             # Array of wavlengths if the sensor.
  pix,           # Pixel number to convert to wavelength.
) -> float:      # The wavelength of the pixel.
  '''
  Return the wavelength of a given pixel index.
  Out of range wavelengths cause -1 to be returned.
  '''
  dw  = (x[-1] - x[0])
  dpx = len(x)
  d  = dw/dpx
  w = px*d + x[0]
  if w < x[0]:
    w = -1.0
  elif w > x[-1]:
    w = -1.0
  return w

# %% ../nbs/00_RedTideProcessing.ipynb 46
def w_range_pixels( 
  x,        # A numpy array of wavlengths for each pixel.
  a,        # Starting wavelength.
  b         # Ending wavelength.
) -> list:  # List of pixels cooresponding to `a`:`b` wavelengths.
    '''
    Returns a pixel index list of all pixels between wavelength 'a' and 'b'. 
    '''
    rv = np.where(np.logical_and( x>a, x<b) )
    return rv

# %% ../nbs/00_RedTideProcessing.ipynb 54
def get_list_of_json_spectra( p        # String path to mission data set.
                            ) ->list:  # List of full paths to each JSON spectra file.
    ''' Returns a list of Json spectra full path filenames found in subdirs under "p". '''
    gstr = f'{p}/*/*/*-spec.json'
    lst = glob.glob(gstr, recursive=True)
    return lst

# %% ../nbs/00_RedTideProcessing.ipynb 58
def json_specs_to_df( specs ):
    '''
    Extracts the hhmmss and fsecs from 'specs' filename, converts
    the hhmmss and fsecs strings to float SOD.fsecs.

    Parameters:
    specs: list  A list of json spectra files.

    Returns:
    --------
    A DataFrame of sod.fsecs:float, hhmmss:str, Json_spec:str
    '''
    # Extract the hhmmss and fsecs from each file name,
    # convert the hhmmss and fsecs to float SOD.fsecs, 
    # and create a list of each.
    hhmmss = []
    fsecs  = []
    sod    = []
    for v in specs:
      tx = extract_hms( v )
      hhmmss.append( tx[0] )   # Build the list if hhmmss strings.
      sod.append( tx[3] )      # Build the list of sod floats.

    # Now convert the  lists to a Pandas dataframe.
    dct = {'sod':sod, 'hhmmss':hhmmss, 'Json_spec':specs}
    df = pd.DataFrame( dct )
    df.sort_values(by=['sod'], inplace=True)              # Sort the data in time order.
    return df

# %% ../nbs/00_RedTideProcessing.ipynb 62
def is_water( x,y):
    '''
    Returns the mean signal value between 840nm and 860nm wavelengths.  Since water absorbs IR.

    Inputs:
      x   A numpy array of wavlengths for each pixel
      y   A numpy array of intensity values at each wavelength.  x and y mus be the same size.

    Returns:
      The mean signal value between 840nm and 860nm.  The signal level is not currently normalized
      for anything, exposure, etc.  Threshold is around 4.0.  Above 4, land or glint.

    References: 
    Application of the water-related spectral reflectance indices: A review
    https://www.sciencedirect.com/science/article/abs/pii/S1470160X18308215

    '''
    rv = y[w_range_pixels(x,840,860)].mean()
    return rv

# %% ../nbs/00_RedTideProcessing.ipynb 64
def wavelength_2_RGB(
  wavelength,   # Wavelength in nanometers.
  alpha=255     # Alpha to use.
) -> list:      # ( red, green, blue )
  '''
  Convert a wavelength to a tuple of red, green, blue values.
  
  From: https://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html
  '''
  w = int(wavelength)

  # colour
  if w >= 380 and w < 440:
      R = -(w - 440.) / (440. - 350.)
      G = 0.0
      B = 1.0
  elif w >= 440 and w < 490:
      R = 0.0
      G = (w - 440.) / (490. - 440.)
      B = 1.0
  elif w >= 490 and w < 510:
      R = 0.0
      G = 1.0
      B = -(w - 510.) / (510. - 490.)
  elif w >= 510 and w < 580:
      R = (w - 510.) / (580. - 510.)
      G = 1.0
      B = 0.0
  elif w >= 580 and w < 645:
      R = 1.0
      G = -(w - 645.) / (645. - 580.)
      B = 0.0
  elif w >= 645 and w <= 780:
      R = 1.0
      G = 0.0
      B = 0.0
  else:
      R = 0.0
      G = 0.0
      B = 0.0

  # intensity correction
  if w >= 380 and w < 420:
      SSS = 0.3 + 0.7*(w - 350) / (420 - 350)
  elif w >= 420 and w <= 700:
      SSS = 1.0
  elif w > 700 and w <= 780:
      SSS = 0.3 + 0.7*(780 - w) / (780 - 700)
  else:
      SSS = 0.0
  SSS *= 255

  return [int(SSS*R), int(SSS*G), int(SSS*B), int(alpha)]

# %% ../nbs/00_RedTideProcessing.ipynb 67
def wavelength_2_RGB_str( 
  wavelength:float,        # Wavelength in nanometers.
  alpha=255                # Alpha, transparency to use.  
) ->str:                   # rgb string such as: "#01abffff"
  '''
  Converts a wavelength to an RGB string suitable to use
  as a color parameter in most applications.
  '''
  rgb  = wavelength_2_RGB(wavelength, alpha=alpha)
  rgbs = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{rgb[3]:02x}'
  return rgbs

# %% ../nbs/00_RedTideProcessing.ipynb 70
Fraunhofer_lines = {
                'A' :[ 'O2', 759.370  ],
                'B' :[ 'O2', 686.719  ], 
                'C' :[ 'Ha', 656.281  ],
                'a' :[ 'O2', 627.661  ],
                'D1':[ 'Na', 589.592  ],
                'D2':[ 'Na', 588.995  ],
                'D3':[ 'He', 587.5618 ],
              'e-hg':[ 'Hg', 546.073  ],
                'E2':[ 'Fe', 527.039  ],
                'b1':[ 'Mg', 518.362  ],
                'b2':[ 'Mg', 517.270  ],
                'b3':[ 'Mg', 516.891  ],
                'b4':[ 'Mg', 516.733  ],
                'c' :[ 'Fe', 495.761  ],                                                            
                'F' :[ 'Hb', 486.134  ],
                'd' :[ 'Fe', 466.814  ],
              'e-Fe':[ 'Fe', 438.355  ],
                'G' :[ 'Fe', 430.790  ],
                'G2':[ 'Ca', 430.774  ],
                'H' :[ 'Ca', 396.847  ] 
}

# %% ../nbs/00_RedTideProcessing.ipynb 74
HG_lines = { 
          'Hg-404' :[ 'Hg', 404.6563 ],
          'Hg-436' :[ 'Hg', 435.8328 ],
          'Hg-543' :[ 'Hg', 543.6    ],
          'Hg-546' :[ 'Hg', 546.0735 ],
          'Hg-576' :[ 'Hg', 576.959  ],
          'Hg-579' :[ 'Hg', 579.065  ],
          'Hg-611' :[ 'Hg', 610.8    ],
          'Hg-615' :[ 'Hg', 614.9475 ]

}

# %% ../nbs/00_RedTideProcessing.ipynb 78
sentinal_s2a = {
# Band
#         Center
#                Width
  'b2' : [ 492.7, 65],
  'b3' : [ 559.8, 35],
  'b4' : [ 664.6, 30],
  'b8' : [ 832.8, 105],
  
  'b5' : [ 704.1, 14],
  'b6' : [ 740.5, 14],
  'b7' : [ 782.8, 19],
  '8a' : [ 864.7, 21],
}

# %% ../nbs/00_RedTideProcessing.ipynb 80
class Sentinal_Band:
  '''
  Defines a single Sentinel band data object. 
  '''
  header = f'band center_nm width_nm color w_low px_low w_high px_high '
  average = True
  mean    = False
  
  def __init__(self,  
               x:list,          # A Numpy array of wavelengths cooresponding to each pixel.
               name:str,        # The Sentinel official wavelength-band name.
               center_nm:float, # Center wavelength in nanometers.
               width_nm:float,  # Bandwidth in nanometers.
               color:str        # Desired color to use for any plots, or graphics.
              ) -> object:      # Class object returned.
    self.name      = name
    self.center_nm = center_nm
    self.width_nm  = width_nm
    self.color     = color
    self.w_low     = center_nm - width_nm/2
    self.w_high    = center_nm + width_nm/2
    self.px_low    = w_to_pixel( x, self.w_low )
    self.px_high   = w_to_pixel(x, self.w_high )
    self.pixels    = w_range_pixels(x, self.w_low,self.w_high)
    self.y_mean    = 0.0        # This gets updated.
  
  def __str__(self):
    return f'{self.name} {self.center_nm:6.2f} {self.width_nm:6.1f} {self.color} '\
           f'{self.w_low:6.1f} {self.px_low:4d} {self.w_high:6.1f} {self.px_high:4d}'
  
  def compute_stats(self, 
                  spectra     # Spectra to update y_mean from.
                 ) -> None:   # The stat values are updated in the class.
    '''
    Compute the Sentinel band stats for a given spectra if enabled. To enable or
    disable set Sentinel_Band.average = True | False, or Sentinel_Band.mean = True | False.
    '''
    if self.mean:
      self.y_mean    = spectra[ self.pixels ].mean()
    else:
      self.y_mean = 0.0
      
    if self.average:
      self.y_average = np.average( spectra[ self.pixels ] )
    else:
      self.y_average = 0.0  

# %% ../nbs/00_RedTideProcessing.ipynb 86
def sentinel_update( 
  spectra,           # Raw spectra to compute Sentinel band averages on.
  sentinel_bands     # Array of sentinel band classes.       
) -> None:           # sentinel_bands will contain .y_mean afterward.
  '''
  '''
  for s in sentinel_bands:
    sentinel_bands[ s ].compute_stats( spectra )

# %% ../nbs/00_RedTideProcessing.ipynb 100
#debug_nearest_rgb_image = False
def nearest_rgb_image( 
  fn,          # Json spectra file.
  debug=False  # True to debug internals.
) -> str:      # File name of the nearest RGB photo to this json spectra.
    """
    Returns the path/filename to the RGB photo closes in time to `fn`.  `fn` is the
    filename of a Json hyperspectral file.

    Parameters:
    -----------
    fn : str
      Full path/filename of a hyperspectral Json file.

    Returns:
    --------
    str
      A string path/filename of the closes RGB photo.

    Examples:
    ---------

    References:
    -----------
    """
    if debug:
      print(f'debug_nearest_rgb_image(fn): fn={fn}')
    fn_parts = fn.split('/')   # Split path by '/'
    if debug:
      print(f'debug_nearest_rgb_image(fn): fn_parts={fn_parts}')
    rgb_p = fn_parts                          # Make a copy to build the rgb path/filename in.
    if debug:
      print(f'debug_nearest_rgb_image(fn): rgb_p={rgb_p}')    
    rgb_p[-2] = 'hab_rgb'                     # Change the subdir to point to hab_rgb
    rgb_fn = rgb_p[-1].split('-')             # Split the filename by '-' to access parts.
    rgb_fn[-2] = '*'                          # Replace the microseconds with '*' wildcard.
    rgb_fn[-1] = 'rgb.jpg'                    # Change the file tail to rgb.jpg
    rgb_p[-1] = '-'.join(rgb_fn)              # Glue the name back together
    rgb_p2 = '/'.join(rgb_p)                  # Now glue the whole path back together
    rv = glob.glob(rgb_p2)[0]                 # Return the first entry incase there are more than 1.
    if debug:
      print(f'debug_nearest_rgb_image(fn): rv={rv}') 
    return rv


# %% ../nbs/00_RedTideProcessing.ipynb 103
#debug_read_gps_file_to_df = False
def read_gps_file_to_df( ifn, debug=False):
    '''
    Read a GPS datafile into a dataframe and convert the HH:MM:SS
    to add an SOD column.

    Parameters:
    -----------
    ifn : str
        Input GPS datafile full path name

    Returns:
    --------
    Pandas Dataframe of the GPS data.
    '''
    gps_df = pd.read_csv(ifn, sep='\s+', comment='#')
    gps_df.sort_values(by=['HMS'], inplace=True)
    # Convert the ASCII HH:MM:SS from the GPS to seconds of the day (SOD) and
    # add an 'SOD' column to the gps dataframe.
    sod_lst = []
    for t in gps_df['HMS']:
      sod_lst.append( hms2sod(t))
    gps_df['SOD'] = sod_lst

    # Compute, and add 'Course' to dataframe
    course = []
    for i in  range(len(gps_df)-1):
      course.append ( get_bearing( 
          lat1=gps_df['Lat'].iloc[i], long1=gps_df['Lon'].iloc[i], 
          lat2=gps_df['Lat'].iloc[i+1], long2=gps_df['Lon'].iloc[i+1] 
          ) 
      )
    course.append( 0.0 )      # To make the same length
    gps_df['Course'] = course
    return gps_df

# %% ../nbs/00_RedTideProcessing.ipynb 107
#debug_compute_gps_positions = False 
def compute_gps_positions(  gps, spec_df, debug=False):
    '''
    Interpolates spectra positions from gps.

    Parameters:
    -----------
    gps : dataframe
        A dataframe of overlapping gps position data.

    spec_df : dataframe
        A dataframe of values vs time from the spectrometer.

    Returns:
    --------
    See: https://numpy.org/doc/stable/reference/generated/numpy.interp.html
    '''
    spec_df['Lat']    = np.interp(spec_df['sod'], gps['SOD'], gps['Lat'])
    spec_df['Lon']    = np.interp(spec_df['sod'], gps['SOD'], gps['Lon'])
    spec_df['Elev']   = np.interp(spec_df['sod'], gps['SOD'], gps['Elev'])
    spec_df['Course'] = np.interp(spec_df['sod'], gps['SOD'], gps['Course'])
    return spec_df

# %% ../nbs/00_RedTideProcessing.ipynb 109
#debug_get_bearing = False
def get_bearing( lat1=0, lat2=0, long1=0, long2=0, debug=False):
    '''
    Comutes and returns the bearing between two lat/lon pairs.
    See:
        http://shorturl.at/atGHN
    '''
    brng = Geodesic.WGS84.Inverse(lat1, long1, lat2, long2)['azi1']
    return brng

# %% ../nbs/00_RedTideProcessing.ipynb 112
#debug_get_list_of_flight_lines = False
def get_list_of_flight_lines( p, debug=False):
    '''Returns a list of flightline subdirs on path p.

    Parameters:
    -----------
    p : str
        Path name.

    Returns:
    --------
    list
        A list of full pathnames to individul flightlines.
    '''
    l = glob.glob(p+'/[0-9]*[!a-z]')
    return l

# %% ../nbs/00_RedTideProcessing.ipynb 116
#debug_get_list_of_hab_files = False
def get_list_of_hab_files( p, subdir='', ext='', debug=False):
    '''Returns a list of hab files in p/subdir with the specified file extension.  
    
    Parameters:
    p : str
    subdir : str Default = ''
    ext : str Default = ''

    Returns:
    --------
    list
        A list of  full pathnames.
    '''
    gs = p+f'/{subdir}/*.'+ext
    js = glob.glob(gs)
    return js

# %% ../nbs/00_RedTideProcessing.ipynb 126
#debug_get_fluorescence = False
def get_fluorescence( x, y, fl_start=0, fl_stop=0, base_start=0, base_stop=0, debug=False ):
    '''
    '''
    fl_sig = y[w_range_pixels(x, fl_start, fl_stop )].mean()         # Get the Fluor signal mean value
    by = y[w_range_pixels(x, base_start, base_start+1)].mean()
    ey = y[w_range_pixels(x, base_stop, base_stop+1)].mean()
    center_nm = (fl_stop - fl_start) / 2  + fl_start                                       # Compute center wavelength
    dydx = (ey - by)/(base_stop - base_start )
    sf = dydx * (center_nm - base_start)
    rv = fl_sig + sf
    if debug:
      print('get_fluorescence():', fl_sig, by, ey, center_nm, dydx, sf, rv)
    return rv

# %% ../nbs/00_RedTideProcessing.ipynb 128
def get_fluorescence_700( x, y):
    '''
    Returns the fluorescence value at 700nm.
    '''
    rv = get_fluorescence( x, y, fl_start=693, fl_stop=710, base_start=668, base_stop=740 )
    return rv

# %% ../nbs/00_RedTideProcessing.ipynb 130
def get_fluorescence_683( x, y):
    '''
    Returns the fluorescence value at 683nm.  683nm is Chlorophyll
    '''
    rv = get_fluorescence( x, y, fl_start=678, fl_stop=688, base_start=668, base_stop=740 )
    return rv
