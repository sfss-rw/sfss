#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Author: 			Robert Wells
# Project Title: 	Smart Firefighter Support System
# FileName: 		SFSS_serial.py
# Path: 			c:\..._2019 Fall\Design 2\GUI\SFSS with Serial\SFSS_serial.py
# Created Date: 	Friday, October 25th 2019, 17:53:41 pm
# -----
# Last Modified: 	Monday, November 18th 2019, 17:42:58 pm
# Modified By: 		Robert Wells
# -----
# Copyright (c) 2019 SFSS
#
# GNU General Public License v3.0
# https://spdx.org/licenses/LGPL-3.0-only.html
# -----
# HISTORY:
# Date      			By		Comments
# ----------			---		----------------------------------------------------------
# 2019-11-18 17:11:04	RW		combined data checking if statements into defs
#                               recoded the popup calls to use windows
#                                   this should eliminate the opening of extraneous popups in the background
# 2019-11-18 12:11:09	RW		added configuration settings for metrics using configparser
#                               req'd adding [ConfigSectionMap] to map the settings.ini file to the right places
# 2019-11-12 14:11:82	RW		cleaned up code, resized elements to make window look cleaner
# 2019-11-11 13:11:80	RW		inserted motor status popup on kris's request [motorWarningPopup]
#                               waiting to test [motorWarningPopup] since the board is not outputting data in the correct format
#                               added break after dataErrorPopup to stop the while loop if there's a data error
# 2019-11-06 11:11:93	RW		added datetime to log file, got rid of 'bool' value for motor (it was showing true when false..?)
#                               added 'index=False' to [logalldata] to set up for graphing
#                               added "newline=''" to [createlogfile] to stop creating a newline after writing header
#
# 2019-10-25 19:10:16	RW		Commented out some imports, some housekeeping
# 2019-10-25 17:10:16	RW		Forgot to keep logging the changes for a while..
#                               COM port communication works
#                               Optimized the code quite a bit to get rid of unneeded lines
#                               Recoded the layout to be a single window as opposed to {setup}&{main}
# 2019-10-06 22:10:29	RW		FIRST ITERATION of sfss with serial data input.
#                               changed input csv format to comply with jonathan's sample output.
#                               added in serial open/close commands for setup window and main tab
###



# ---------------------------------- imports --------------------------------- #

import csv
import os
import subprocess
import sys
import time
import webbrowser
# from datetime import datetime
import datetime as dt

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
import PySimpleGUI as sg
import serial
import serial.tools.list_ports
from matplotlib.ticker import MaxNLocator

from configparser import SafeConfigParser

# import io
# import argparse
# import numpy as np
# import random
# from random import randrange
# from random import randint
# from multiprocessing import Process
# from multiprocessing import Pipe
# import multiprocessing

# * DEPENDENCY: matplotlib 3.0.3
# * [env conda activate seniordesigngui]

# // FIXME: motor status is True all the time? check into the df

# TODO: test motorWarningPopup when board code is updated
# TODO: add updating 'gif' or progress meter for connection
# TODO: add indicator for connection on/off
# // TODO: add hr sensor's built in graphing if possible
# TODO: add right click menus for (raw data, initialize connection, export photo?)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                    GLOBALS                                   #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# serial globals
# BAUDRATE=115200
# TIMEOUT=2
# ser=serial.Serial()

# ---------------------------------------------------------------------------- #
#                                  Definitions                                 #
# ---------------------------------------------------------------------------- #


# --------------------------- connection setup defs -------------------------- #

def statusWarningPopup(ffnum, status, color):
    """Warning popup called if values recieved is out of bounds

    Args:
        ffnum (str): string used to indicate firefighter number within popup
        status (str): string used to indicate warning type within popup
        color (str): string used to set the background color of the popup to differentiate warning tytpe
    """
    # sg.PopupAutoClose('{} Warning for {}'.format(status,ffnum), auto_close_duration=2, non_blocking=True,
    # background_color= color, grab_anywhere=True, keep_on_top=False, location=(-1,-1))
    sg.popup_no_wait('{} Warning for {}'.format(status,ffnum), auto_close=True, auto_close_duration=15, non_blocking=True,
    background_color= color, grab_anywhere=True, keep_on_top=False, location=(1,60))


def dataErrorPopup(ffnum):
    sg.PopupAutoClose('Something went wrong', "There was an error with {}'s data".format(ffnum), non_blocking=True, auto_close_duration=2)

def motorWarningPopup(m_warn1, m_warn2=None):
    sg.PopupAutoClose('Motor Warning', "Warning: These sensors [{}, {}] are not generating valid data".format(m_warn1,m_warn2))

def portError():
    sg.PopupAutoClose('Something went wrong', 'Make sure you have the correct port selected in the list box', non_blocking=True, auto_close_duration=2)

# NOTE: leaving this here just in case
    # def ExecutePortList(command, *args):
    #     """executes commands through cmd.exe, used here to call powershell to get a list of available COM ports


    #     Args:
    #         command (string): [command to be passed to cmd.exe]
    #     """
    #     try:
    #         sp = subprocess.Popen([command, *args], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         out, err = sp.communicate()
    #         if out:
    #         #     #portlist = out.decode('utf-8')
    #             print(out.decode("utf-8"))
    #         if err:
    #             print(err.decode("utf-8"))
    #     except:
    #         sg.PopupError('executeportlist error')

    #     return (out)

def ExecutePortList():
    """
    vid and pid for the XBee S2C are stored here.
    if this model is used, configuration should be easier, requiring less user input
    if a different model is used, the user would need to figure out which COM port their
    device is using (probably using cmd.exe and switch it manually with the combobox

    """
    ## XBee S2C device vendor and part numbers
    vid="0403"
    pid="6015"
    #sernum="DN069Y7GA"
    device_found = False
    my_com_port = None
    description = None

    ports = list(serial.tools.list_ports.comports())

    for p in ports:
        try:
            if vid and pid in p.hwid:
                description = p.hwid
                my_com_port = p.device
                device_found = True
                return(my_com_port, description, device_found)
        except:
            print('The SFSS device wasnt found :(')
            print('We use the Vendor Number and Part Number to locate it.')
            print('Are you using the original device [XBee S2C]?')
            print("If not, refer to 'About'-'Help' from the menu above")
            break
    # print(my_comm_port)


# def ExecutePortConfigure(command, *args):
#     print = window.element('_SETUPOUTPUT_').Update
#     try:
#         sp = subprocess.call([command, *args], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         out, err = sp.communicate()
#         if out:
#             print('\n', out.decode("utf-8"))
#         if err:
#             print(err.decode("utf-8"))

#         return (out, err)
#     except:
#         pass

# ----------------------------- file writing defs ---------------------------- #

def serialToList(ser):
    """converts recieved serial data into a list

    Args:
        ser (variable): ser, (i.e. ser = serial.Serial())
    """

    decoded_parsed_rawdata = ser.readline().decode('utf-8').split()
    ser.flushInput()
    # decoded_parsed_rawdata_time = (date_time + decoded_parsed_rawdata)
    return(decoded_parsed_rawdata)

def listToDataFrame(datalist):

    header = ['microcntr', 'temp', 'movement', 'fall', 'heartrate', 'motor']
    # bool_columns = ['motor']
    float_columns = ['temp', 'movement', 'fall', 'heartrate']
    dataframe = pd.DataFrame([datalist], columns = header, index=None)
    # dataframe[bool_columns] = dataframe[bool_columns].astype(bool)
    dataframe[float_columns] = dataframe[float_columns].astype(float)
    #dataframe.index = pd.Series([dt.datetime.now()] * len(dataframe)) ##adds timestamp to dataframe and sets as index
    return(dataframe)

def logAllData(dataframe, ffnumber):

    dataframe.to_csv(ffnumber, sep=',', float_format='%04f', mode='a', header=None, index=False)

def createLogFile(filename):
    """creates an initial log file, and places "logheader" at the top

    Args:
        filename (string): name for the file
    """
    # setting header for the log csv
    logheader = ['microcntr', 'temp', 'movement', 'fall', 'heartrate', 'motor']
    logfile_name=filename+"_"+str(dt.datetime.now().strftime("%Y-%m-%d %H%M%S"))+'.log'
    with open(logfile_name,'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(logheader)
        return logfile_name
        #print('done with header')

# ----------------------------- HEART RATE TABLE ----------------------------- #

def hrtable1():
    sg.SetOptions(auto_size_buttons=True)
    filename = sg.PopupGetFile('Choose the .CSV with the data you want to see', no_window=False,
    file_types=(("CSV Files", "*.csv"),))
    # --- populate table with file contents --- #
    if filename == '':
        sys.exit(69)
    data = []
    header_list = []
    if filename is not None:
        try:
            df = pd.read_csv(filename, sep=',', engine='python', header=None)
            # Header=None means you directly pass the columns names to the dataframe
            data = df.values.tolist()
            # read everything else into a list of rows
            header_list = df.iloc[0].tolist()
            # Uses the first row (which should be column names) as columns names
            data = df[1:].values.tolist()
            # Drops the first row in the table (otherwise the header names and the first row will be the same)
        except:
            sg.PopupError('Error reading file')
            pass

    hr_table_layout = [[sg.Table(values=data, headings=header_list, display_row_numbers=False, auto_size_columns=True, num_rows=min(25,len(data)))]]
    hrwindow = sg.Window('FF1 HR Table', grab_anywhere=False)
    while True:
        event, values = hrwindow.Layout(hr_table_layout).Read()
        if event in(None, 'Exit'):
            break
    pass
    # def hrtable1():
    #     print('hrtable1')
    #     sg.SetOptions(auto_size_buttons=True)
    #     df = pd.read_csv('data1.csv', names = ['time', 'heartrate'], index_col=['time'])
    #     print('file read')
    #     data = df.values.tolist()
    #     header_list = df.iloc[0].tolist()
    #     data = df[1:].values.tolist()


    #     hr_table_layout = [[sg.Table(values=data, headings = header_list, display_row_numbers=False, auto_size_columns=True, num_rows=min(25,len(data)))]]

    #     hrtable = sg.Window('FF1 HR Table', grab_anywhere=False)

    #     while True:
    #         event, values = hrtable.Layout(hr_table_layout).Read()
    #         if event in(None, 'Exit'):
    #             break
        #pass


    # def hrtable1():
    #     hr=pd.read_csv('data1.csv', names=['Time', 'HR'])
    #     if hr == None:
    #         print('error reading file')
    #         sys.exit('Error Reading File')
    #     data = []
    #     header_list = hr.iloc[0].tolist()
    #     if hr is not None:
    #         try:
    #             data = hr.values.tolist()
    #         except:
    #             sg.PopupError('Error Reading File')
    #             pass

# ------------------------------ MOVEMENT TABLE ------------------------------ #

def movtable1():
    sg.SetOptions(auto_size_buttons=True)
    filename = sg.PopupGetFile('Choose the .CSV with the data you want to see', no_window=False,
    file_types=(("CSV Files", "*.csv"),))
    # --- populate table with file contents --- #
    if filename == '':
        sys.exit(69)
    data = []
    header_list = []
    if filename is not None:
        try:
            df = pd.read_csv(filename, sep=',', engine='python', header=None)
            data = df.values.tolist()
            header_list = df.iloc[0].tolist()
            data = df[1:].values.tolist()
        except:
            sg.PopupError('Error reading file')
            pass

    mov_table_layout = [[sg.Table(values=data, headings=header_list, display_row_numbers=False,
                            auto_size_columns=True, num_rows=min(25,len(data)))]]

    movwindow = sg.Window('Table', grab_anywhere=False)
    while True:
        event, values = movwindow.Layout(mov_table_layout).Read()
        if event in(None, 'Exit'):
            break
    pass

# ------------------------------- Warning LEDs ------------------------------- #

def LEDIndicator(key=None, radius=40):
    """draws the "LEDs" on each tab by utilizing tkinter's canvas

    Args:
        key (str, optional): indicates where to draw using the items key. Defaults to None.
        radius (int, optional): size of the canvas. Defaults to 40.

    Returns:
        canvas: the LED
    """
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key)

def SetLED(window, key, color):
    """function to set the LED. called when a status change is experienced

    Args:
        window (None): defines which sg.window to update
        key (str): defines which element in the window
        color (str): what color to set the LED
    """
    graph = window.FindElement(key)
    graph.Erase()
    graph.DrawCircle((0, 0), 20, fill_color=color, line_color=color)

def setLEDStatus(w, fftabkey, maintabkey, color):
    """this function calls SetLED to change both of a FF's LED's at once. only put here to avoid typing SetLED twice


    Args:
        w (none): defines which sg.Window to update
        fftabkey (str): key value for the FF's personal LED
        maintabkey (str): key value for the FF's LED on the 'main' tab
        color (str): color to set the LED
    """
    SetLED(w, fftabkey, color)
    SetLED(w, maintabkey, color)
# ----------------------------- HEART RATE GRAPHS ---------------------------- #
# def showHrGraph(datalist):

#     # Parameters
#     x_len = 200         # Number of points to display
#     y_range = [0, 250]  # Range of possible Y values to display

#     # Create figure for plotting
#     fig = plt.figure()
#     ax = fig.add_subplot(1, 1, 1)
#     xs = list(range(0, 200))
#     ys = [0] * x_len
#     ax.set_ylim(y_range)

#     # Initialize communication with TMP102
#     #tmp102.init()

#     # Create a blank line. We will update the line in animate
#     line, = ax.plot(xs, ys)

#     # Add labels
#     plt.title('Heart Rate Over Time')
#     plt.xlabel('Samples')
#     plt.ylabel('HR (BPM)')

# # This function is called periodically from FuncAnimation
#     def animate(i, ys):

#         # Read temperature (Celsius) from TMP102
#         #temp_c = round(tmp102.read_temp(), 2)
#         hr = datalist[-2]
#         # hr = datalist
#         # Add y to list
#         ys.append(hr)

#         # Limit y list to set number of items
#         ys = ys[-x_len:]

#         # Update line with new Y values
#         line.set_ydata(ys)

#         return line,

# # below is function call
# # Set up plot to call animate() function periodically
#     ani = animation.FuncAnimation(fig,
#         animate,
#         fargs=(ys,),
#         interval=50,
#         blit=True)
#     plt.show(block=False)

    # sg.SetOptions(auto_size_buttons=True)

    # hr_layout = [[sg.Table(values=data, headings=header_list, display_row_numbers=False, auto_size_columns=True, num_rows=min(25,len(data)))]]
    # hr_window = sg.Window('Heartrate', grab_anywhere=False)
    # while True:
    #     event, values = hrwindow.Layout(hr_table_layout).Read()
    #     if event in(None, 'Exit'):
    #         break
def showhr2graph():
    x=[]
    y=[]
    with open('data2.csv',  encoding = 'utf-8-sig') as csvfile:
        plots = csv.reader(csvfile)
        for data in plots:
            #get heading for x and y axes
            var1 = ('Time')
            var2 = ('Heart Rate (bpm)')
            break
        for data in plots:
            #get values - add to x list and y list
            x.append(float(data[0]))
            y.append(float(data[1]))

    ax = plt.subplot(1,1,1)
    ax.set_ylim([0, 280])
    ax.xaxis.set_major_locator(MaxNLocator(10))
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    plt.plot(x,y, label = 'HR')
    plt.axhline(y  = 230, color = 'red', linestyle = '--', label = 'Danger')
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.title('FireFighter 2: Heart Rate')

    plt.legend()
    plt.show()

def showhr3graph():
    x=[]
    y=[]
    with open('data3.csv',  encoding = 'utf-8-sig') as csvfile:
        plots = csv.reader(csvfile)
        for data in plots:
            #get heading for x and y axes
            var1 = ('Time')
            var2 = ('Heart Rate (bpm)')
            break
        for data in plots:
            #get values - add to x list and y list
            x.append(float(data[0]))
            y.append(float(data[1]))

    ax = plt.subplot(1,1,1)
    ax.set_ylim([0, 280])
    ax.xaxis.set_major_locator(MaxNLocator(10))
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    plt.plot(x,y, label = 'HR')
    plt.axhline(y  = 230, color = 'red', linestyle = '--', label = 'Danger')
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.title(' FireFighter 3: Heart Rate')


    plt.legend()
    plt.show()

# ------------------------------- configuration ------------------------------ #

config = SafeConfigParser()
config.sections()
config.read('settings.ini')

def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def checkHeartRate(ffhrdf, upper_thresh, lower_thresh, caut_thresh, fftab_LEDkey, maintab_LEDkey, ffnum, popups, window):

    if  ffhrdf.item() <= lower_thresh or ffhrdf.item() >= upper_thresh:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'red')

        hr_pop = True
        close_hr_pop = False
        # if not popups:
        #     pass
        # else:
        #     statusWarningPopup(ffnum,'Heart Rate', 'firebrick')

    elif caut_thresh < ffhrdf.item() < upper_thresh:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'orange')

        hr_pop = False
        close_hr_pop = True
    else:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'green')

        hr_pop = False
        close_hr_pop = True
    return hr_pop, close_hr_pop



def checkMovement(ffmovdf, upper_thresh, lower_thresh, fftab_LEDkey, maintab_LEDkey, warning_key, ffnum, popups, window):

    if  ffmovdf == upper_thresh:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'red')
        window[warning_key].Update('Low movement')

        mov_pop = True
        close_mov_pop = False
        # if not popups:
        #     pass
        # else:
        #     statusWarningPopup(ffnum,'Movement', 'darkorange')
    else:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'green')
        window[warning_key].Update('No warnings')

        mov_pop = False
        close_mov_pop = True

    return mov_pop, close_mov_pop

def checkTemperature(fftempdf, upper_thresh, lower_thresh, caut_thresh, fftab_LEDkey, maintab_LEDkey, warning_key, ffnum, popups, window):
    
    if  fftempdf.item() > upper_thresh:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'red')
        window[warning_key].Update('High Temperature')

        temp_pop = True
        close_temp_pop = False
        # if not popups:
        #     pass
        # else:
        #     statusWarningPopup(ffnum,'Temperature', 'orangered')

    elif caut_thresh < fftempdf.all() < upper_thresh:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'orange')
        window[warning_key].Update('Moderate Temperature')

        temp_pop = False
        close_temp_pop = True

    else:
        setLEDStatus(window, fftab_LEDkey, maintab_LEDkey, 'green')
        window[warning_key].Update('No warnings')

        temp_pop = False
        close_temp_pop = True

    return temp_pop, close_temp_pop

# ---------------------------------------------------------------------------- #
#                                 PROGRAM START                                #
# ---------------------------------------------------------------------------- #


def main():
    BAUDRATE=115200 # ! trying moving these here to  get rid of called before assignment
    TIMEOUT=2
    ser=serial.Serial()

# ---------------------------- setup window "feel" --------------------------- #

    sg.ChangeLookAndFeel('Dark2')
    sg.SetOptions(font=('calibri', 12,), element_padding=(1, 1))

# ------------------------- get pathname for logo file ----------------------- #

    dirname, filename = os.path.split(os.path.abspath(__file__))
    pathname = os.path.join(dirname, 'logo.png')

# ------------------------------ Menu Definition ----------------------------- #

    menu_def = [['File', ['Setup Connection::_SETUP_', 'Terminate Connection::_TERMINATE_', 'Save', 'Exit'  ]],
                ['Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                ['Help', ['Users Guide', 'About...']], ]

# ---------------------------------------------------------------------------- #
#                                 GUI Defintion                                #
# ---------------------------------------------------------------------------- #

# --------------------- define columns to be used in tabs -------------------- #

 # --------------------------------- main tab --------------------------------- #

    comlist = ['-------', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8',
                'COM9', 'COM10', 'COM11', 'COM12', 'COM13', 'COM14', 'COM15']

    cold1_frame_layout = [
        [sg.Output(size=(52, 25), key='_SETUPOUTPUT_',pad=((0,0),(10,5)), font='Courier 8')],
        [sg.Button('Check COM Ports', pad=(5,10), bind_return_key=False),
         sg.Button('Configure COM Port', pad=(5,10), bind_return_key=False, button_color=('white', 'green')),
         sg.DropDown(comlist, size=(10,1), enable_events=True, readonly=True, key='_LISTBOX_')]
    ]

    cold1 = [[sg.Frame('Setup', layout = cold1_frame_layout, relief=sg.RELIEF_RAISED, pad=(0,2), element_justification='center')]]

    cold2_frame_layout = [
        [sg.Text('Firefighter #',   pad=((0, 20),(30,10)), justification='center'), 
        sg.Text('Heart Rate',       pad=((0, 20),(30,10)), justification='center'),
        sg.Text('Movement',         pad=((0, 20),(30,10)), justification='center'), 
        sg.Text('Temperature',      pad=((0, 20),(30,10)), justification='center')],

        [sg.Text('Firefighter 1: ', pad=((2, 2),(20,20)), justification='left'),
        sg.Text(' ', pad=(( 0, 10),(20,40))),   LEDIndicator('_TABDEFAULTFF1HRLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF1MOVLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF1TEMPLED_')],

        [sg.Text('Firefighter 2: ', pad=((2, 2),(20,20)), justification='left'), 
        sg.Text(' ', pad=(( 0, 10),(20,40))),   LEDIndicator('_TABDEFAULTFF2HRLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF2MOVLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF2TEMPLED_')],

        [sg.Text('Firefighter 3: ', pad=((2, 2),(20,20)), justification='left'), 
        sg.Text(' ', pad=(( 0, 10),(20,40))),   LEDIndicator('_TABDEFAULTFF3HRLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF3MOVLED_'),
        sg.Text(' ', pad=((35, 20),(20,40))),   LEDIndicator('_TABDEFAULTFF3TEMPLED_')],
        
        [sg.Button('Update All', pad=(5,15), key='_UPDATEALL_'), sg.Button('Stop Updates', pad=(5,15), key='_TABDEFAULTSTOPUP_'),
         sg.Checkbox('Enable PopUps', default = True, enable_events = True, key='_TOGGLEPOPUPALL_')]
         ]

    cold2 = [[sg.Frame('Firefighter Status', cold2_frame_layout, relief=sg.RELIEF_RAISED, element_justification='justified')]]

 # ----------------------------------- tab 1 ---------------------------------- #

    cola1_frame_layout = [
        [sg.Text("Status", font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF1HRLED_'), sg.Text(' ', pad=((0, 10),(10,10))),
        sg.Multiline(size=(15,1),font=('calibri', 15, 'bold'), disabled=True, key='_HRTEXT1_', pad=((0, 10),(20,20))),
        sg.Text('Max Recorded HR:', pad=((10, 49),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MAXHRTEXT1_', pad=((0, 10),(20,20))),
        # sg.Button('Plot HR', key='_PLOTHR1_')]
        ]]

    cola1 = [[sg.Frame('Heart Rate', cola1_frame_layout, element_justification='center')]]

    cola2_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF1MOVLED_'), sg.Text(' ', pad=((0, 10),(10,10))),
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVTEXT1_', pad=((0, 10),(20,20))),
        sg.Text('Movement Warnings:', pad=((10, 34),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVWARN1_', pad=((0, 10),(20,20))),
        ]
    ]

    cola2 = [[sg.Frame('Movement', cola2_frame_layout)]]

    cola3_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF1TEMPLED_'), sg.Text(' ', pad=((0, 10),(10,10))),
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPTEXT1_', pad=((0, 10),(20,20))),
        sg.Text('Temperature Warnings:', pad=((10, 20),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPWARN1_', pad=((0, 10),(20,20))),
        ]
    ]

    cola3 = [[sg.Frame('Temperature', cola3_frame_layout)]]

    cola4 = [[sg.Button('Update',       pad=(10,4), key='_UPDATETAB1_'), 
              sg.Button('Stop Updates', pad=(10,4), key='_STOPUPTAB1_'), 
              sg.Button('Show Graph',   pad=(10,4), key='_PLOTHR1_')]]

 # ----------------------------------- tab 2 ---------------------------------- #

    colb1_frame_layout = [
        [sg.Text("Status", font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF2HRLED_'), sg.Text(' ', pad=((0, 10),(10,10))),
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_HRTEXT2_', pad=((0, 10),(20,20))),
        sg.Text('Max Recorded HR:', pad=((10, 49),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MAXHRTEXT2_', pad=((0, 10),(20,20))),
        # sg.ReadButton('Plot HR', key='_PLOTHR2_')]
        ]
    ]

    colb1 = [[sg.Frame('Heart Rate', colb1_frame_layout, element_justification='center')]]

    colb2_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF2MOVLED_'), sg.Text(' ', pad=((0, 10),(10,10))), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVTEXT2_', pad=((0, 10),(20,20))),
        sg.Text('Movement Warnings:', pad=((10, 34),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVWARN2_', pad=((0, 10),(20,20))),
        ]
    ]

    colb2 = [[sg.Frame('Movement', colb2_frame_layout)]]

    colb3_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF2TEMPLED_'), sg.Text(' ', pad=((0, 10),(10,10))), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPTEXT2_', pad=((0, 10),(20,20))),
        sg.Text('Temperature Warnings:', pad=((10, 20),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPWARN2_', pad=((0, 10),(20,20))),
        ]
    ]

    colb3 = [[sg.Frame('Temperature', colb3_frame_layout, element_justification='center')]]

    colb4 = [[sg.Button('Update',       pad=(10,4), key='_UPDATETAB2_'), 
              sg.Button('Stop Updates', pad=(10,4), key='_STOPUPTAB2_'), 
              sg.Button('Show Graph',   pad=(10,4), key='_PLOTHR2_')]]

 # ----------------------------------- tab 3 ---------------------------------- #

    colc1_frame_layout = [
        [sg.Text("Status", font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF3HRLED_'), sg.Text(' ', pad=((0, 10),(10,10))), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_HRTEXT3_', pad=((0, 10),(20,20))),
        sg.Text('Max Recorded HR:', pad=((10, 49),(2,2)), justification='right'), 
        sg.Multiline(size=(10,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MAXHRTEXT3_', pad=((0, 10),(20,20))),
        # sg.ReadButton('Plot HR', key='_PLOTHR3_')]
        ]
    ]

    colc1 = [[sg.Frame('Heart Rate', colc1_frame_layout)]]

    colc2_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF3MOVLED_'), sg.Text(' ', pad=((0, 10),(10,10))), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVTEXT3_', pad=((0, 10),(20,20))),
        sg.Text('Movement Warnings:', pad=((10, 34),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_MOVWARN3_', pad=((0, 10),(20,20))),
        ]
    ]

    colc2 = [[sg.Frame('Movement', colc2_frame_layout)]]

    colc3_frame_layout = [
        [sg.Text('Status', font=('calibri', 12), pad=((2, 20),(2,2)), justification='right'),
        LEDIndicator('_FF3TEMPLED_'), sg.Text(' ', pad=((0, 10),(10,10))), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPTEXT3_', pad=((0, 10),(20,20))),
        sg.Text('Temperature Warnings:', pad=((10, 20),(2,2)), justification='right'), 
        sg.Multiline(size=(15,1), font=('calibri', 15, 'bold'), disabled=True,  key='_TEMPWARN3_', pad=((0, 10),(20,20))),
        ]
    ]

    colc3 = [[sg.Frame('Temperature', colc3_frame_layout)]]

    colc4 = [[sg.Button('Update',       pad=(10,4), key='_UPDATETAB3_'), 
              sg.Button('Stop Updates', pad=(10,4), key='_STOPUPTAB3_'), 
              sg.Button('Show Graph',   pad=(10,4), key='_PLOTHR3_')]]

# ---------------------------- define tab layouts ---------------------------- #

    tabdefault_layout = [
                    [sg.Text('Welcome to the SFSS!', size=(45, 1), justification='center', font=('calibri', 25, 'bold'))],
                    [sg.Column(cold1), sg.Column(cold2)]
    ]

    tab1_layout =  [
                    [sg.Text('Firefighter 1', font=('calibri', 15, 'bold'))],
                    [sg.Column(cola1, justification='center', element_justification='center')],
                    [sg.Column(cola2, justification='center', element_justification='center')],
                    [sg.Column(cola3, justification='center', element_justification='center')],
                    [sg.Column(cola4, justification='center', element_justification='center')],
                    # [sg.Button('Update', key='_UPDATETAB1_'), sg.Button('Stop Updates', key='_STOPUPTAB1_'),
                    # sg.Button('Show Graph', key='_PLOTHR1_')]
    ]

    tab2_layout =  [
                    [sg.Text('Firefighter 2', font=('calibri', 15, 'bold'))],
                    [sg.Column(colb1, justification='center', element_justification='center')],
                    [sg.Column(colb2, justification='center', element_justification='center')],
                    [sg.Column(colb3, justification='center', element_justification='center')],
                    [sg.Column(colb4, justification='center', element_justification='center')],
    ]

    tab3_layout =  [
                    [sg.Text('Firefighter 3', font=('calibri', 15, 'bold'))],
                    [sg.Column(colc1, justification='center', element_justification='center')],
                    [sg.Column(colc2, justification='center', element_justification='center')],
                    [sg.Column(colc3, justification='center', element_justification='center')],
                    [sg.Column(colc4, justification='center', element_justification='center')],
    ]

# ------------------------------- window layout ------------------------------ #

    layout = [
        [sg.Menu(menu_def, tearoff=False)],
        [sg.TabGroup([
            [sg.Tab('Welcome', tabdefault_layout),
             sg.Tab('Firefighter 1', tab1_layout),
             sg.Tab('Firefighter 2', tab2_layout),
             sg.Tab('Firefighter 3', tab3_layout)]
            ],
            key='_TABGROUP_', title_color='Black')]
    ]

    # window = sg.Window("Smart Firefighter Support System", default_element_size=(20, 5), auto_size_text=False,
    #                         auto_size_buttons=True, element_padding=(2,2), grab_anywhere=False,
    #                         default_button_element_size=(5, 1), resizable=True, element_justification='center',
    #                         finalize=True).Layout(layout)

    window = sg.Window("Smart Firefighter Support System", element_justification='left', location=(1,145),
                            finalize=True).Layout(layout)

# ------------------------------ initialize LEDs ----------------------------- #

    window.Finalize()
    SetLED(window, '_TABDEFAULTFF1HRLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF1MOVLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF1TEMPLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF2HRLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF2MOVLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF2TEMPLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF3HRLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF3MOVLED_', 'grey')
    SetLED(window, '_TABDEFAULTFF3TEMPLED_', 'grey')

    SetLED(window, '_FF1HRLED_', 'grey')
    SetLED(window, '_FF1MOVLED_', 'grey')
    SetLED(window, '_FF1TEMPLED_', 'grey')
    SetLED(window, '_FF2HRLED_', 'grey')
    SetLED(window, '_FF2MOVLED_', 'grey')
    SetLED(window, '_FF2TEMPLED_', 'grey')
    SetLED(window, '_FF3HRLED_', 'grey')
    SetLED(window, '_FF3MOVLED_', 'grey')
    SetLED(window, '_FF3TEMPLED_', 'grey')

# -------------------------------- pre-launch -------------------------------- #

   # ---------------------- load settings from settings.ini --------------------- #

    FF1_HR_UPPER        = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_hr_upper'])
    FF1_HR_LOWER        = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_hr_lower'])
    FF1_HR_CAUTION      = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_hr_caution'])
    FF1_MOV_UPPER       = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_mov_upper'])
    FF1_MOV_LOWER       = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_mov_lower'])
    FF1_TEMP_UPPER      = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_temp_upper'])
    FF1_TEMP_LOWER      = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_temp_lower'])
    FF1_TEMP_CAUTION    = int(ConfigSectionMap("Firefighter 1 Thresholds")['ff1_temp_caution'])

    FF2_HR_UPPER        = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_hr_upper'])
    FF2_HR_LOWER        = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_hr_lower'])
    FF2_HR_CAUTION      = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_hr_caution'])
    FF2_MOV_UPPER       = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_mov_upper'])
    FF2_MOV_LOWER       = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_mov_lower'])
    FF2_TEMP_UPPER      = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_temp_upper'])
    FF2_TEMP_LOWER      = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_temp_lower'])
    FF2_TEMP_CAUTION    = int(ConfigSectionMap("Firefighter 2 Thresholds")['ff2_temp_caution'])

    FF3_HR_UPPER        = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_hr_upper'])
    FF3_HR_LOWER        = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_hr_lower'])
    FF3_HR_CAUTION      = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_hr_caution'])
    FF3_MOV_UPPER       = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_mov_upper'])
    FF3_MOV_LOWER       = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_mov_lower'])
    FF3_TEMP_UPPER      = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_temp_upper'])
    FF3_TEMP_LOWER      = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_temp_lower'])
    FF3_TEMP_CAUTION    = int(ConfigSectionMap("Firefighter 3 Thresholds")['ff3_temp_caution'])

   # -------------------------- initialize empty lists -------------------------- #

    ff1_list = []
    #ff2_list = []
    #ff3_list = []

   # ------------------------------ start log files ----------------------------- #

    ff1_logfile = createLogFile('FF1')
    #ff2 = createLogFile('FF2') # NOTE: need to add this to ff
    #ff3 = createLogFile('FF3') # NOTE: need to add this to ff

   # --------------------------- print welcome message -------------------------- #

    print(" >>> Welcome to the SFSS")
    print(" >>> 1. Plug in the SFSS to a USB port")
    print(" >>> 2. Click the Check COM Ports button")
    print(" >>> 3. Follow the instructions that show up here")

# -------------------------------- event loop -------------------------------- #

    hrpopup1_active = False
    movpopup1_active = False
    temppopup1_active = False

    hrpopup2_active = False
    movpopup2_active = False
    temppopup2_active = False

    hrpopup3_active = False
    movpopup3_active = False
    temppopup3_active = False

    while True:
        event, values = window.Read()

        if event in (None, 'Exit'):
            #if ser.is_open:
            ser.close()
            # keeplog(ff1_log)
            break

# ------------------------------ showing graphs ------------------------------ #

        # if event == '_HRGRAPH1_':
        #     plt.ion()
        #     plt.show()
        #     fig = plt.figure()
        #     ax1 = fig.add_subplot(1,1,1)
        #     def animate(i):
        #         pullData = open("data1.csv","rb").read()
        #         dataArray = pullData.split('\n')
        #         xar = []
        #         yar = []
        #         for eachLine in dataArray:
        #             if len(eachLine)>1:
        #                 x,y = eachLine.split(',')
        #                 xar.append(int(x))
        #                 yar.append(int(y))
        #         ax1.clear()
        #         ax1.plot(xar,yar)
        #     ani = animation.FuncAnimation(fig, animate, interval=1000)
        #     # plt.ion()
        #     # plt.show()
        #     plt.draw()
        #     plt.pause(.1)
        # if event == '_HRGRAPH2_':
        #     showhr2graph()
        # if event == '_HRGRAPH3_':
        #     showhr3graph()

# ---------------------------------------------------------------------------- #
#                      warning LEDs and outputting status                      #
# ---------------------------------------------------------------------------- #

# ------------------------------- FIREFIGHTER1 ------------------------------- #

    # ------------------------------- updating FF1 ------------------------------- #

        if event == '_UPDATETAB1_' or event =='_UPDATEALL_':
            try:
                file_update_ff1 = 1
                ser.open()
            except:
                sg.PopupError('make sure you set up the COM port first')
                continue

            while True:
                event, values = window.Read(timeout=250)

                if event in(None, 'Exit'):
                    ser.close()
                    break

                elif event == '_STOPUPTAB1_' or event=='_TABDEFAULTSTOPUP_':
                    file_update_ff1 = not file_update_ff1
                    ser.close()
                    break

                elif file_update_ff1:
                    popups_enabled = values['_TOGGLEPOPUPALL_']
                    try:
                        # time.sleep(.01)
                        # createLogFile('ff1.log')
                        ff1_list = serialToList(ser)
                        ff1_hr_list = ff1_list[-2]
                        # print(ff1_list)
                        # print(ff1_hr_list)
                        df1 = listToDataFrame(ff1_list)
                        logAllData(df1, ff1_logfile)
                        # print(df1)

                        # keeplog(ff1_log)

                        # ff1_hr_graph_list =
                        motor_status_1 = df1['motor'].iloc[0]
                        ff1_heartrate = df1['heartrate'].iloc[0]
                        window['_HRTEXT1_'].Update(df1['heartrate'].iloc[0])

    # ------------------------------- FF1 hr graph ------------------------------- #

                        # if event == '_PLOTHR1_':            # ! try creating a window for this process like the old cmd window
                        #     # showHrGraph(ff1_list)

                        #     # Parameters
                        #     # popups_enabled=False
                        #     x_len = 200         # Number of points to display
                        #     y_range = [0, 250]  # Range of possible Y values to display

                        #     # Create figure for plotting
                        #     fig = plt.figure()
                        #     ax = fig.add_subplot(1, 1, 1)
                        #     xs = list(range(0, 200))
                        #     ys = [0] * x_len
                        #     ax.set_ylim(y_range)

                        #     # Initialize communication with TMP102
                        #     #tmp102.init()

                        #     # Create a blank line. We will update the line in animate
                        #     line, = ax.plot(xs, ys)

                        #     # Add labels
                        #     plt.title('Heart Rate Over Time')
                        #     plt.xlabel('Samples')
                        #     plt.ylabel('HR (BPM)')

                        # # This function is called periodically from FuncAnimation
                        #     def animate(i, ys):

                        #         # Read temperature (Celsius) from TMP102
                        #         #temp_c = round(tmp102.read_temp(), 2)
                        #         # hr = int(ff1_list[-2])
                        #         hr = round(ff1_list[-2])
                        #         # hr = ff1_hr_list
                        #         # Add y to list
                        #         ys.append(hr)

                        #         # Limit y list to set number of items
                        #         ys = ys[-x_len:]

                        #         # Update line with new Y values
                        #         line.set_ydata(ys)

                        #         return line,

                        # # below is function call
                        # # Set up plot to call animate() function periodically
                        #     ani = animation.FuncAnimation(fig,
                        #         animate,
                        #         fargs=(ys,),
                        #         interval=50,
                        #         blit=True)
                        #     plt.show(block=False)
                        # else:
                        #     pass

    # ------------------------------- update maxhr ------------------------------- #

                        if  values['_HRTEXT1_'] > values['_MAXHRTEXT1_']:
                            window['_MAXHRTEXT1_'].Update(values['_HRTEXT1_'])
                        else:
                            pass

    # ---------------------------- update motor status --------------------------- #

                        if motor_status_1 != 0:
                            try:
                                if motor_status_1 == 1:
                                    # motorWarningPopup('Heart Rate')
                                    print('The motor is active because of Heart Rate')
                                    pass
                                elif motor_status_1 == 2:
                                    # motorWarningPopup('Temperature')
                                    print('The motor is active because of Temperature')
                                    pass
                                elif motor_status_1 == 3:
                                    # motorWarningPopup('Heart Rate', 'Temperature')
                                    print('The motor is active because of Heart Rate and Temperature')
                                    pass
                            except:
                                pass
                        else:
                            pass

    # --------------------------------- FF1heartrate -------------------------------- #

                        hr_popup1, close_hr_popup1 = checkHeartRate(ff1_heartrate, FF1_HR_UPPER, FF1_HR_LOWER, FF1_HR_CAUTION, 
                                                                            '_FF1HRLED_', '_TABDEFAULTFF1HRLED_', 'FF1', popups_enabled, window)


                        if popups_enabled:
                            if hr_popup1 and not hrpopup1_active:
                                hrpopup1_active = True
                                layout_hr1 = [
                                            [sg.Text('HR Warning for FF1')],
                                            [sg.Button('OK')]
                                            ]
                                hrpopup1 = sg.Window('Warning', size=(275, 100), location=(1000,145), font=('white'), 
                                                    background_color='firebrick', use_default_focus=False).Layout(layout_hr1)
        
                            if hrpopup1_active and close_hr_popup1:
                                hrpopup1_active = False
                                hrpopup1.close()
                            else:
                                pass

                            if hrpopup1_active:
                                event, values = hrpopup1.read(timeout=0)
                                if event == 'Exit' or event is None:
                                    hrpopup1_active = False
                                    hrpopup1.close()
                                    pass
                        else:
                            if hrpopup1_active:
                                hrpopup1_active = False
                                hrpopup1.close()
                            pass
    # --------------------------------- FF1movement --------------------------------- #

                        ff1_movement = df1['movement'].iloc[0]
                        window['_MOVTEXT1_'].Update(df1['movement'].iloc[0])

                        mov_popup1, close_mov_popup1 = checkMovement(ff1_movement, FF1_MOV_UPPER, FF1_MOV_LOWER, 
                                                                            '_FF1MOVLED_', '_TABDEFAULTFF1MOVLED_', '_MOVWARN1_', 'FF1', popups_enabled, window)

                        if popups_enabled:
                            if mov_popup1 and not movpopup1_active:
                                movpopup1_active = True
                                layout_mov1 = [
                                            [sg.Text('Movement Warning for FF1')],
                                            [sg.Button('OK')]
                                            ]
                                movpopup1 = sg.Window('Warning', size=(275, 100), location=(1000,265), font=('white'), 
                                                    background_color='darkorange', use_default_focus=False).Layout(layout_mov1)
        
                            if movpopup1_active and close_mov_popup1:
                                movpopup1_active = False
                                movpopup1.close()
                            else:
                                pass

                            if movpopup1_active:
                                event, values = movpopup1.read(timeout=0)
                                if event == 'Exit' or event is None:
                                    movpopup1_active = False
                                    movpopup1.close()
                                    pass
                        else:
                            if movpopup1_active:
                                movpopup1_active = False
                                movpopup1.close()
                            pass

    # -------------------------------- FF1temperature ------------------------------- #

                        ff1_temperature = df1['temp'].iloc[-1]
                        window['_TEMPTEXT1_'].Update(ff1_temperature)

                        temp_popup1, close_temp_popup1 = checkTemperature(ff1_temperature, FF1_TEMP_UPPER, FF1_TEMP_LOWER, FF1_TEMP_CAUTION, 
                                                                            '_FF1TEMPLED_', '_TABDEFAULTFF1TEMPLED_', '_TEMPWARN1_', 'FF1', popups_enabled, window)

                        if popups_enabled:
                            if temp_popup1 and not temppopup1_active:
                                temppopup1_active = True
                                layout_temp1 = [
                                            [sg.Text('Temperature Warning for FF1')],
                                            [sg.Button('OK')]
                                            ]
                                temppopup1 = sg.Window('Warning', size=(275, 100), location=(1000,385), font=('white'), 
                                                    background_color='orangered', use_default_focus=False).Layout(layout_temp1)
        
                            if temppopup1_active and close_temp_popup1:
                                temppopup1_active = False
                                temppopup1.close()
                            else:
                                pass

                            if temppopup1_active:
                                event, values = temppopup1.read(timeout=0)
                                if event == 'Exit' or event is None:
                                    temppopup1_active = False
                                    temppopup1.close()
                                    pass

                        else:
                            if temppopup1_active:
                                temppopup1_active = False
                                temppopup1.close()
                            pass

    # -------------------------- plotting ff1 heart rate ------------------------- #

                        if event == '_PLOTHR1_':
                            try:            # ! try creating a window for this process like the old cmd window
                                # showHrGraph(ff1_list)

                                # Parameters
                                # popups_enabled=False
                                x_len = 400         # Number of points to display
                                # y_range = [0, 250]  # Range of possible Y values to display
                                y_range = [0,200]     #! temporary range of y values b/c hr sensor is not working
                                # Create figure for plotting
                                fig = plt.figure()
                                ax = fig.add_subplot(1, 1, 1)
                                xs = list(range(0, 400))
                                ys = [0] * x_len
                                ax.set_ylim(y_range)
                                # ser.flushInput()
                                # Initialize communication with TMP102
                                #tmp102.init()

                                # Create a blank line. We will update the line in animate
                                line, = ax.plot(xs, ys)

                                # Add labels
                                plt.title('Heart Rate Over Time')
                                plt.xlabel('Samples')
                                plt.ylabel('HR (BPM)')

                                # This function is called periodically from FuncAnimation
                                def animate(i, ys):

                                    # Read temperature (Celsius) from TMP102
                                    #temp_c = round(tmp102.read_temp(), 2)
                                    # hr = int(ff1_list[-2])
                                    hr = ff1_hr_list
                                    # Add y to list
                                    ys.append(hr)

                                    # Limit y list to set number of items
                                    ys = ys[-x_len:]

                                    # Update line with new Y values
                                    line.set_ydata(ys)

                                    return line,

                                # below is function call
                                # Set up plot to call animate() function periodically
                                ani = animation.FuncAnimation(fig,
                                    animate,
                                    fargs=(ys,),
                                    interval=100,
                                    blit=True)
                                plt.show(block=False)
                            except:
                                break
                        else:
                            pass

                    except:
                        # if not dataError:
                        dataErrorPopup('FF1')
                        print('\n >>> There seems to be an error with transmitting the data.\n >>> Try resetting the SFSS and try again')
                        break
                #ser.flushInput()
                # time.sleep(.1)

# ------------------------------- FIREFIGHTER2 ------------------------------- #

    # ------------------------------- updating FF2 ------------------------------- #

        if event == '_UPDATETAB2_' or event =='_UPDATEALL_':
            file_update_ff2 = 1

            while True:
                event, values = window.Read(timeout=500)
                if event is None:
                    break
                elif event == '_STOPUPTAB2_' or event=='_TABDEFAULTSTOPUP_':
                    file_update_ff2 = not file_update_ff2
                    break
                elif file_update_ff2:
                    df2 = pd.read_csv('data2.csv', names=['time', 'heartrate'], index_col=['time'])
                    maxhr2 = df2['heartrate'].max()
                    last_row_display2 = df2['heartrate'].iloc[-1]
                    window['_HRTEXT2_'].Update(last_row_display2)
                    window['_MAXHRTEXT2_'].Update(maxhr2)

    # --------------------------------- FF2heartrate -------------------------------- #


                    if last_row_display2.item() >= 230:
                        SetLED(window, '_FF2HRLED_', 'red' if last_row_display2.all() > 230 else 'red')
                        SetLED(window, '_TABDEFAULTFF2HRLED_', 'red' if last_row_display2.all() > 230 else 'red')
                        sg.PopupAutoClose('WARNING! HEART RATE IS HIGH!', auto_close_duration=3, non_blocking=True,
                        background_color='firebrick',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(600,150))
                    elif last_row_display2.item() <=50:
                        SetLED(window, '_FF2HRLED_', 'red' if last_row_display2.all() <= 50  else 'red')
                        SetLED(window, '_TABDEFAULTFF2HRLED_', 'red' if last_row_display2.all() <= 50 else 'red')
                        sg.PopupAutoClose('WARNING! HEART RATE IS LOW!', auto_close_duration=3, non_blocking=True,
                        background_color='lightblue',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(600,150))
                    elif last_row_display2.item() > 200 and last_row_display2.item() < 230:
                        SetLED(window, '_FF2HRLED_', 'orange' if last_row_display2.all()  > 200 and last_row_display2.all() <230  else 'orange')
                        SetLED(window, '_TABDEFAULTFF2HRLED_', 'orange' if last_row_display2.all()  > 200 and last_row_display2.all() <230  else 'orange')
                    else:
                        SetLED(window, '_FF2HRLED_', 'green' if last_row_display2.all() < 230 else 'green')
                        SetLED(window, '_TABDEFAULTFF2HRLED_', 'green' if last_row_display2.all() < 230 else 'green')

    # --------------------------------- FF2movement --------------------------------- #

                    df2m = pd.read_csv('data2mov.csv', names=['time', 'movement'], index_col=['time'])
                    #movwarn1 = df1['movement'].max()
                    last_row_display2m = df2m['movement'].iloc[-1]
                    window['_MOVTEXT2_'].Update(last_row_display2m)
                    if last_row_display2m.item() < 1:
                        window['_MOVWARN2_'].Update('Low movement')
                        SetLED(window, '_FF2MOVLED_', 'red' if last_row_display2m.all() < 1 else 'red')
                        SetLED(window, '_TABDEFAULTFF2MOVLED_', 'red' if last_row_display2.all() < 1 else 'red')
                        sg.PopupAutoClose('WARNING! LOW MOVEMENT DETECTED!', auto_close_duration=3, non_blocking=True,
                        background_color='darkorange',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(750,150))
                    else:
                        window['_MOVWARN2_'].Update('No warnings')
                        SetLED(window, '_FF2MOVLED_', 'green' if last_row_display2m.all() > 1 else 'green')
                        SetLED(window, '_TABDEFAULTFF2MOVLED_', 'green' if last_row_display2m.all() > 1 else 'green')

    # -------------------------------- FF2temperature ------------------------------- #

                    df2t = pd.read_csv('data2temp.csv', names=['time', 'temp'], index_col=['time'])
                    #movwarn2 = df2['movement'].max()
                    last_row_display2t = df2t['temp'].iloc[-1]
                    window['_TEMPTEXT2_'].Update(last_row_display2t)
                    if last_row_display2t.item() > 500:
                        window['_TEMPWARN2_'].Update('High Temperature')
                        SetLED(window, '_FF2TEMPLED_', 'red' if last_row_display2t.all() > 500 else 'red')
                        SetLED(window, '_TABDEFAULTFF2TEMPLED_', 'red' if last_row_display2.all() > 500 else 'red')
                        sg.PopupAutoClose('WARNING! HIGH TEMPERATURE DETECTED!', auto_close_duration=3, non_blocking=True,
                        background_color='orangered',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(450,150))
                    elif last_row_display2t.item() > 400 and last_row_display2t.item() < 500:
                        window['_TEMPWARN2_'].Update('Moderate Temperature')
                        SetLED(window, '_FF2TEMPLED_', 'orange' if last_row_display2t.all()  > 400 and last_row_display2t.all() < 500  else 'orange')
                        SetLED(window, '_TABDEFAULTFF2TEMPLED_', 'orange' if last_row_display2t.all()  > 400 and last_row_display2t.all() < 500  else 'orange')
                    else:
                        window['_TEMPWARN2_'].Update('No warnings')
                        SetLED(window, '_FF2TEMPLED_', 'green' if last_row_display2t.all() < 500 else 'green')
                        SetLED(window, '_TABDEFAULTFF2TEMPLED_', 'green' if last_row_display2t.all() < 500 else 'green')

# ------------------------------- FIREFIGHTER3 ------------------------------- #

    # ------------------------------- updating FF3 ------------------------------- #

        if event == '_UPDATETAB3_' or event =='_UPDATEALL_':

            file_update_ff3 = 1

            while True:
                event, values = window.Read(timeout=500)
                if event is None:
                    break
                elif event == '_STOPUPTAB2_' or event=='_TABDEFAULTSTOPUP_':
                    file_update_ff3 = not file_update_ff3
                    break
                elif file_update_ff3:
                    df3 = pd.read_csv('data3.csv', names=['time', 'heartrate'], index_col=['time'])
                    maxhr3 = df3['heartrate'].max()
                    last_row_display3 = df3['heartrate'].iloc[-1]
                    window['_HRTEXT3_'].Update(last_row_display3)
                    window['_MAXHRTEXT3_'].Update(maxhr3)

    # ------------------------------- FF3heartrate ------------------------------- #

                    if last_row_display3.item() >= 230:
                        SetLED(window, '_FF3HRLED_', 'red' if last_row_display3.all() > 230  else 'red')
                        SetLED(window, '_TABDEFAULTFF3HRLED_', 'red' if last_row_display3.all() > 230 else 'red')
                        sg.PopupAutoClose('WARNING! HEART RATE IS HIGH!', auto_close_duration=3, non_blocking=True,
                        background_color='firebrick',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(600,150))
                    elif last_row_display3.item() <=50:
                        SetLED(window, '_FF3HRLED_', 'red' if last_row_display3.all() <= 50  else 'red')
                        SetLED(window, '_TABDEFAULTFF3HRLED_', 'red' if last_row_display3.all() <= 50 else 'red')
                        sg.PopupAutoClose('WARNING! HEART RATE IS LOW!', auto_close_duration=3, non_blocking=True,
                        background_color='lightblue',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(600,150))
                    elif last_row_display3.item() > 200 and last_row_display3.item() < 230:
                        SetLED(window, '_FF3HRLED_', 'orange' if last_row_display3.all()  > 200 and last_row_display3.all() <230  else 'orange')
                        SetLED(window, '_TABDEFAULTFF3HRLED_', 'orange' if last_row_display3.all()  > 200 and last_row_display3.all() <230  else 'orange')
                    else:
                        SetLED(window, '_FF3HRLED_', 'green' if last_row_display3.all() < 230 else 'green')
                        SetLED(window, '_TABDEFAULTFF3HRLED_', 'green' if last_row_display3.all() < 230 else 'green')

    # --------------------------------- FF3movement --------------------------------- #

                    df3m = pd.read_csv('data3mov.csv', names=['time', 'movement'], index_col=['time'])
                    #movwarn1 = df1['movement'].max()
                    last_row_display3m = df3m['movement'].iloc[-1]
                    window['_MOVTEXT3_'].Update(last_row_display3m)
                    if last_row_display3m.item() < 1:
                        window['_MOVWARN3_'].Update('Low movement')
                        SetLED(window, '_FF3MOVLED_', 'red' if last_row_display3m.all() < 1 else 'red')
                        SetLED(window, '_TABDEFAULTFF3MOVLED_', 'red' if last_row_display3.all() < 1 else 'red')
                        sg.PopupAutoClose('WARNING! LOW MOVEMENT DETECTED!', auto_close_duration=3, non_blocking=True,
                        background_color='darkorange',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(750,150))
                    else:
                        window['_MOVWARN3_'].Update('No warnings')
                        SetLED(window, '_FF3MOVLED_', 'green' if last_row_display3m.all() > 1 else 'green')
                        SetLED(window, '_TABDEFAULTFF3MOVLED_', 'green' if last_row_display3m.all() > 1 else 'green')

    # -------------------------------- FF3temperature ------------------------------- #

                    df3t = pd.read_csv('data3temp.csv', names=['time', 'temp'], index_col=['time'])
                    #movwarn3 = df3['movement'].max()
                    last_row_display3t = df3t['temp'].iloc[-1]
                    window['_TEMPTEXT3_'].Update(last_row_display3t)
                    if last_row_display3t.item() > 500:
                        window['_TEMPWARN3_'].Update('High Temperature')
                        SetLED(window, '_FF3TEMPLED_', 'red' if last_row_display3t.all() > 500 else 'red')
                        SetLED(window, '_TABDEFAULTFF3TEMPLED_', 'red' if last_row_display3.all() > 500 else 'red')
                        sg.PopupAutoClose('WARNING! HIGH TEMPERATURE DETECTED!', auto_close_duration=3, non_blocking=True,
                        background_color='orangered',  font=('calibri', 15, 'bold'), grab_anywhere=True, keep_on_top=False, location=(450,150))
                    elif last_row_display3t.item() > 400 and last_row_display3t.item() < 500:
                        window['_TEMPWARN3_'].Update('Moderate Temperature')
                        SetLED(window, '_FF3TEMPLED_', 'orange' if last_row_display3t.all()  > 400 and last_row_display3t.all() < 500  else 'orange')
                        SetLED(window, '_TABDEFAULTFF3TEMPLED_', 'orange' if last_row_display3t.all()  > 400 and last_row_display3t.all() < 500  else 'orange')
                    else:
                        window['_TEMPWARN3_'].Update('No warnings')
                        SetLED(window, '_FF3TEMPLED_', 'green' if last_row_display3t.all() < 500 else 'green')
                        SetLED(window, '_TABDEFAULTFF3TEMPLED_', 'green' if last_row_display3t.all() < 500 else 'green')

# ----------------------------------- setup ---------------------------------- #

        if event == 'Check COM Ports':
            # foo = ExecutePortList('powershell', '[System.IO.Ports.SerialPort]::getportnames()')
            print('Searching for your device...\n')
            try:
                foo, desc, found = ExecutePortList()

                if found:
                    print(' >>> SFSS Found!')
                    print(' >>> Device: ', desc)
                    print(" \n >>> Your COM port is: {} \n >>> Click 'Configure COM Port'".format(foo))
                if not found:
                    print(" >>> Device not found. Refer to the 'Help' section in the menu above")
            except TypeError:
                print("We're having trouble finding your SFSS")
                print("Are you sure it's connected?\n")
            window.Refresh()

        if event == 'Configure COM Port':
            try:
                foo, desc, found = ExecutePortList()
                ser = serial.Serial()
                ser.baudrate=BAUDRATE
                ser.timeout=TIMEOUT

                if found:
                    try:
                        #portToConfig = foo
                        print('\nConfiguring', foo)
                        ser.port = foo
                        if not ser.is_open:
                            ser.open()
                        print('\n >>> The port opened is: {}'.format(ser.name))
                        print(' >>> The Baudrate is: {}'.format(ser.baudrate))
                        print(' >>> The Bytesize is: {}'.format(ser.bytesize))
                        print(' >>> The Parity is: {}'.format(ser.parity))
                        print(' >>> Is it readable?: {}'.format(ser.readable()))
                        print(' >>> Is the port really open??: {}'.format(ser.is_open))
                        print(' >>> SUCESS!!')
                        print(' >>> You have been configured to work with the SFSS!')
                        ser.close()
                        pass
                    except:
                        print(' >>> Unable to automatically configure your port.')
                        print(" >>> Select {} in the combobox and click 'Configure COM Port'".format(foo))
                        pass

                if not found:
                    if values['_LISTBOX_'] == '-------':
                        print('\n >>> Your device is unable to be configured automatically')
                        print(" >>> 1. Select {} from the ComboBox below".format(foo))
                        print(" >>> 2. Click 'Configure COM Port'")
                    try:
                        if values['_LISTBOX_'] is not '-------':
                            portToConfig = values['_LISTBOX_']
                            print('\n >>> The port you have selected is: ', portToConfig)
                            print('\nConfiguring', portToConfig)
                            ser.port = portToConfig
                            if not ser.is_open:
                                ser.open()
                            print(' >>> The port opened is: {}'.format(ser.name))
                            print(' >>> The Baudrate is: {}'.format(ser.baudrate))
                            print(' >>> The Bytesize is: {}'.format(ser.bytesize))
                            print(' >>> The Parity is: {}'.format(ser.parity))
                            print(' >>> Is it readable?: {}'.format(ser.readable()))
                            print(' >>> Is the port really open??: {}'.format(ser.is_open))
                            print(' >>> SUCESS!!')
                            print(' >>> You have been configured to work with the SFSS!')
                            ser.close()
                            pass
                    except:
                        portError()
            except:
                portError()

# ------------------------------- menu choices ------------------------------- #

        if event == 'About...':
            sg.Popup('About this program', 'Version 0.1a', 'Smart Firefighter Support System (SFSS)', 'Robert Wells', 'Kris Perales', 'Jonathan Naranjo (PM)', 'Summer Abdullah')
        if event == 'Users Guide':
            # ----------- Subprocess to launch browser and take to SFSS github ----------- #
            CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            FIREFOX = r"C:\Program Files\Mozilla Firefox\firefox.exe"
            github = "https://github.com/rob-wells/sfss/"
            layout = [[sg.Text('GUIDE: https://github.com/rob-wells/sfss/', key='_TEXT_')],
                    [sg.Input('https://github.com/rob-wells/sfss/', do_not_clear=True, key='_URL_')],
                    [sg.Button('Default', bind_return_key=True, focus=True), sg.Button('Chrome'), sg.Button('Firefox')]]
            windowguide = sg.Window("github: User's Guide", layout)
            while True:             # Event Loop
                event, values = windowguide.Read()
                if event in (None, 'Exit'):
                    break
                if event == 'Chrome':
                    sp1 = subprocess.Popen([CHROME, values['_URL_']], shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                if event == 'Firefox':
                    sp2 = subprocess.Popen([FIREFOX, values['_URL_']], shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                # --------------- Use import webbrowser to open default browser --------------- #
                if event == 'Default':
                    webbrowser.open_new(github)
        elif event == 'Open':
            filename = sg.PopupGetFile('file to open', no_window=True)
            print(filename)

# ---------------------------------- way out --------------------------------- #

    # while True:
    #     event, values = window.Read()
    #     print(event, values)
    #     if event in(None, 'Exit'):        # always,  always give a way out!
    #         break

if __name__ == '__main__':
    main()
