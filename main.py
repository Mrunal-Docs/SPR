import argparse
import sys
import time
import socket
import thorlabs_apt as apt
import numpy as np
from datetime import datetime
import pylablib as pll
import statistics
import pyvisa as visa
import math
import matplotlib.pyplot as plt
import csv

#import matplotlib.pyplot as plt

##################################################
#############  DEFAULT SETTING ###################
##################################################


DEFAULT_IP = '169.254.99.134'
# id for testing
# DEFAULT_ID = 27502657
# id for retro reflector DRIVER
DEFAULT_ROTATION_ID = 90251075
DEFAULT_TRANSLATION_ID = 90251076
DEFAULT_WINDOW = 2000
DEFAULT_ACQUISITION_TIME = 20
DEFAULT_FOLDER = 'C:/Users/IQSE/Desktop/SPDC/1216/'


#################################
def check_host(address, port):
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((str(address), port))
        s.settimeout(None)
        return True
    except socket.error as e:
        return False




def main():
    try:

        parser = argparse.ArgumentParser()
        parser.add_argument('--rID', type=int, default=DEFAULT_ROTATION_ID, help='Rotation Stage id')
        parser.add_argument('--tID', type=int, default=DEFAULT_TRANSLATION_ID, help='Translation Stage id')
        args = parser.parse_args()
        motor1 = apt.Motor(args.rID) #establish connection with rotation stage
        motor2 = apt.Motor(args.tID) #establish connection with translation stage

        #Oscilloscope
        from pylablib.devices import Tektronix
        osc = Tektronix.DPO2000("USB0::0x0699::0x03A1::C010231::INSTR")  # #establish connection with oscilloscope
        print('DPO 2022B connection established')

        osc.enable_channel([1])  # Enable channel 1
        osc.set_horizontal_span(0.4)  # Sets the time of acquisition for 1 milliseconds (10^6 samples) , resolution is hzt_span/10
        osc.set_vertical_span("CH1", 5)  # Sets the vertical span of the voltage levels, resolution is vertical_span/10

        #stages (rotation, translation)
        motor1.set_hardware_limit_switches(1,1) #enable forward and reverse motion for rotation stage
        motor1.set_stage_axis_info(-360,360,2,5.454545) #set min pos, max pos, units to deg, pitch rotation stage
        motor2.set_hardware_limit_switches(1,1) #enable forward and reverse motion for translation stage
        motor2.set_stage_axis_info(-100,100,1,1.0) #set min pos, max pos, units to deg, pitch translation stage
        motor2.set_velocity_parameters(0.0, 0.5, 1.0)
        # motor1.move_to() #Home position
        motor2.move_to(0) #Home position
        while motor1.is_in_motion:
            time.sleep(1)
        print('Prism position',motor1.position, 'deg')
        while motor2.is_in_motion:
            time.sleep(1)
        print('Detector position',motor2.position,'mm')


        #Loop scanning to collect voltage data for various incidence angle.
        # motor1.move_by(10) #start taking readings from this position
        # while motor1.is_in_motion:
        #     time.sleep(1)
        print('ready to scan from', motor1.position, 'deg')

        motor2.move_to(13.5)  # start taking readings from this position
        while motor2.is_in_motion:
            time.sleep(1)
        print('ready to scan from', motor2.position, 'mm')

        prism_angle = []
        V_output = []
        angularSteps = 160
        d_theta = 0.1
        for i in range(angularSteps):

            theta = motor1.position
            v = []
            p=[]
            translationSteps = 30
            for j in range(translationSteps) : #loop to scan for the max voltage
                motor2.move_by(0.1)
                p.append(motor2.position)
                while motor2.is_in_motion:
                    time.sleep(2)
                print('j=',j,motor2.position)
                time.sleep(1)
                # Transfers the data to the computer to be read
                rm = visa.ResourceManager()
                scope = rm.open_resource('USB0::0x0699::0x03A1::C010231::INSTR')
                voltage = float(scope.query('MEASU:MEAS1:VAL?'))
                time.sleep(1)
                print(voltage)
                v.append(voltage)

            while motor2.is_in_motion:  # wait
                time.sleep(1)

            maximum_volts = max(v)  # find the maximum voltage.
            max_index = v.index(maximum_volts) # find the index of maximum voltage.
            print(v)
            print('max volts', maximum_volts ,'V found at position',p[max_index],'mm\n' )
            prism_angle.append(theta) #add the current rotational motor angle into the list
            V_output.append(maximum_volts) #add the corresponding max voltage into the list

            motor1.move_by(-d_theta) # Move to next angular position of the prism
            while motor1.is_in_motion: #wait
                time.sleep(1)


            motor2.move_to(p[max_index]) #go to the position of max voltage
            while motor2.is_in_motion:#wait
                time.sleep(1)

            print('Detector ready to scan from', motor2.position)
            print('Prism angular position changed to', motor1.position)

        print(prism_angle, 'deg')
        print(V_output, 'V (max)')
        osc.close()

        #plot the output
        plt.plot(prism_angle,V_output)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.show()

        # data = open('D:\Mrunal\data.csv', 'w')
        # writer = csv.writer(data)
        # for i in range(len(V_output)):
        #     print(i, 'i')
        #     writer.writerow(prism_angle[i])
        # data.close()


        #homing
        motor1.move_to(0.6191)
        motor2.move_to(50) #move it back to 50 to verify laser position goes into iris

        total_time = time.time() - start_time
        print("Execution time =", total_time)


    except BaseException as err:
        print("An exception occurred")
        print(err)
        print(prism_angle, 'deg')
        print(V_output, 'V')
        plt.plot(prism_angle, V_output)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.show()
        osc.close()





if __name__ == '__main__':
    now = datetime.now()

    start_time = time.time()
    main()




