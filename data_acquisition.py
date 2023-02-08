import tkinter as tk
import serial
import serial.tools.list_ports as ser_list
from threading import Thread
import time
from tkinter import Canvas, messagebox
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv 
import numpy as np 

'''Class serial_data was based upon the code written 
by "The Poor Enginer" who does a very nice 
tutorial on how to read serial data at this website 
https://thepoorengineer.com/en/arduino-python-plot/#python. 
This code makes for an excellent starting point for novices
wanting to read seial data using classes.'''

'''Elements for dealing with start stoping the animation of the plot 
were created using this stackoverflow 
question 
https://stackoverflow.com/questions/43812036/placing-an-animated-graph-in-tkinter-gui-via-a-button-push'''

'''THE OBJECT TO DEAL WITH THE SERIAL DATA'''

# Class for dealing with the Serial data 
class serial_data():
    def __init__(self, serial_port = "", serial_baud = 9600):
        self.port = serial_port
        self.baud = serial_baud
        self.is_run = True
        self.is_receiving = False
        self.thread = None
        self.disp = []
        self.load = []
        self.serial_connect = serial.Serial(serial_port, serial_baud, timeout=4)
    
    # Start reading Serial data using background thread
    def read_serial_start(self):
        if self.thread == None:
            self.thread = Thread(target=self.background_thread)
            self.thread.start()
            # Block untill start receiving values
            while self.is_receiving != True:
                time.sleep(0.1)
    
    # Retrieve data
    def background_thread(self): 
        time.sleep(0.1)  # give some buffer time for retrieving data
        self.serial_connect.reset_input_buffer()
        while (self.is_run):
            self.packet = self.serial_connect.readline().decode('utf').rstrip()
            self.is_receiving = True  

    # Process recieved data
    def serial_data(self):
            try:
                self.data =[float(i) for i in self.packet.split("\t")]
            except:
                self.data = [[],[]]

    def send_serial_data(self, data):
        self.serial_connect.write(data)

    # Close the serial connection   
    def close(self):
        self.is_run = False
        self.serial_connect.close()
        print('Disconnected...')    
        
'''THE OBJECT FOR THE GUI'''

# Class for dealing with the GUI
class App():
    def __init__(self, master):
        global state
        self.master = master
        state = True
        self.aquire = False
        self.ani = None
        self.disp_final = []
        self.load_final = []

        # Read cal factor from file ****the cal file must be altered to the directory where cal.txt is stored*****
        with open("/SET PATH TO WORKING DIRECTORY/cal.txt") as f:
            cal_string = f.readlines()
            for i in cal_string:
                numbers = i.split(' ')
            self.cal_factor = float(numbers[0])
            self.cal_b = float(numbers[1])
            

        # Set zero to 0
        self.x0 = 0
        self.zero_load = 0
        # Average for seting new x0
        self.average_int = 20
    
        # Frames 
        self.frame_bg1 = tk.Frame(master, bg="#DCE4E6")
        self.frame_bg1.grid(column = 0, row = 0,sticky = "NW")

        self.frame_1 = tk.LabelFrame(self.frame_bg1,  bg="#DCE4E6", text = "Connection",
        borderwidth=1, font="Helvetica 11 bold")
        self.frame_1.grid(column = 0, row = 0, sticky = "NW", padx = 10, pady = 10)

        self.frame_2 = tk.LabelFrame(self.frame_bg1,  bg="#DCE4E6", text = "Test Type",
        borderwidth=1, font="Helvetica 11 bold")
        self.frame_2.grid(column = 0, row = 1, sticky = "NW", padx = 10, pady = 10)

        self.frame_3 = tk.LabelFrame(self.frame_bg1, text = "Sensor Controls", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_3.grid(column = 0, row = 2, sticky = "NW", padx = 10, pady = 10)

        self.frame_4 = tk.LabelFrame(self.frame_bg1, text = "Save", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_4.grid(column = 0, row = 3, sticky = "NW", padx = 10, pady = 10)


        #Buttons for Serial connect
        self.com_label = tk.Label(self.frame_1, text = "Availible Ports",
         bg="#DCE4E6", font="Helvetica 8 bold")
        self.com_label.grid (column = 0, row = 0, padx = 2, pady = 10)

        self.refresh_but = tk.Button(self.frame_1, text = "Refresh", 
        height = 1, width = 8, command = self.refresh)
        self.refresh_but.grid(column = 2, row = 0, padx= 5, pady = 10)

        self.connect_but = tk.Button(self.frame_1, text = "Connect", 
        height = 1, width = 8, command = self.connect)
        self.connect_but.grid(column = 0, row = 1, padx= 10, pady = 10)

        self.connect_but = tk.Button(self.frame_1, text = "Disconect", 
        height = 1, width = 8, command = self.disconect)
        self.connect_but.grid(column = 1, row = 1, padx= 10, pady = 10)
                
             # Populate list with availible ports 
        self.ports = ser_list.comports()
        self.coms = [com[0] for com in self.ports]
        self.coms.insert(0, "-")

            # Selecting the COM drop button
        self.clicked_com = tk.StringVar()
        self.clicked_com.set(self.coms[0])
        self.drop_COM = tk.OptionMenu(self.frame_1, self.clicked_com, *self.coms)
        self.drop_COM.grid (column = 1, row = 0, padx= 2, pady = 5)

        # Test type buttons 
        self.test_option = tk.IntVar() 
        self.rad_butt_1 = tk.Radiobutton(self.frame_2, text= "Tension", font='Helvetica 10 bold',
        variable= self.test_option, value = 1, bg="#DCE4E6")
        self.rad_butt_1.grid(column=0, row = 1, pady = 5, sticky = "W")
        self.rad_butt_2 = tk.Radiobutton(self.frame_2, text= "Compression", font='Helvetica 10 bold',
        variable= self.test_option, value = 2, bg="#DCE4E6")
        self.rad_butt_2.grid(column=1, row = 1, pady = 5, sticky = "W")


        #plot
         # Plot 1 
        self.fig_1 = Figure(figsize=(7,4), dpi=100, tight_layout = True)
        self.ax1 = self.fig_1.add_subplot(111)
        self.ax1.set_xlabel("Displacement (mm)")
        self.ax1.set_ylabel("Force (N)")
        self.ax1.plot([],[])       
    
        self.canvas1 = FigureCanvasTkAgg(self.fig_1,master=master)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().grid(row=0,column=1,padx=5, pady = 5)

        # Buttons sensor control
        self.start_but = tk.Button(self.frame_3, text = "Start", 
        height = 1, width = 8, command = self.start_data)
        self.start_but.grid(column = 0, row = 0, padx= 10, pady = 10)

        self.stop_but = tk.Button(self.frame_3, text = "Stop", 
        height = 1, width = 8, command = self.stop_data)
        self.stop_but.grid(column = 1, row = 0, padx= 10, pady = 10)

        self.tare_disp_but = tk.Button(self.frame_3, text = "Tare Disp", 
        height = 1, width = 8, command = self.tare_disp)
        self.tare_disp_but.grid(column= 0, row = 2, padx= 10, pady = 10)

        self.tare_load_but = tk.Button(self.frame_3, text = "Tare Load", 
        height = 1, width = 8,command = self.tare_load)
        self.tare_load_but.grid(column= 1, row = 2, padx= 10, pady = 10)

        self.aquire_but = tk.Button(self.frame_3, text = "Aquire Data", 
        height = 1, width = 10,command = self.aquire_data)
        self.aquire_but.grid(column= 0, row = 3, padx= 10, pady = 10)

        self.clear_plot_but = tk.Button(self.frame_3, text = "Clear Plot", 
        height = 1, width = 10, command = self.clear_all)
        self.clear_plot_but.grid(column= 1, row = 3, padx= 10, pady = 10)

        # Live text updates for sensor control
        self.disp_text = tk.StringVar()
        self.disp_text.set("---")
        self.label = tk.Label(self.frame_3, textvariable=self.disp_text, 
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=0, row = 1, padx=10, pady=10)

        self.load_text = tk.StringVar()
        self.load_text.set("---")
        self.label = tk.Label(self.frame_3, textvariable=self.load_text,
         bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=1, row = 1, padx=10, pady=10)

        # Save button
        self.save = tk.Button(self.frame_4, text = "Save Data", height = 1, width = 8, 
        command = self.file_save)
        self.save.grid(column = 0, row = 0, padx = 20, pady = 10)

    '''FUNCTIONS TO MAKE THE GUI WORK'''
    # Function to refresh list of ports 
    def refresh(self):
        self.ports = ser_list.comports()
        self.coms.insert(0, "-")
        self.coms = [com[0] for com in self.ports]
        
        self.drop_COM = tk.OptionMenu(self.frame_1, self.clicked_com, *self.coms)
        self.drop_COM.grid (column = 1, row = 0, padx= 2, pady = 5)
        
    # Function to initiate the serial connection 
    def connect(self):
        print(self.clicked_com.get())
        port_name = self.clicked_com.get()
        baud_rate = 9600
        global s
        s = serial_data(port_name, baud_rate)
        

    # Function to process data from serial class
    def handle_data(self):
        #Apply calibration factor to the raw load readout 
        
        self.cal_load =round(self.cal_b+self.cal_factor*(s.data[1]), 3)


        if self.test_option.get() == 1:
            self.disp = -(s.data[0])
            self.load = -round(self.cal_load-self.zero_load, 3)
        else:
            self.disp = s.data[0]
            self.load = round(self.cal_load-self.zero_load, 3)

        if self.aquire == True:
            self.disp_final.append(self.disp)
            self.load_final.append(self.load)


    # Function to close serial connection 
    def disconect(self):
        s.close()

    # Function to start animation of graph
    def start_ani(self):
        self.ani = animation.FuncAnimation(
            self.fig_1,
            self.update_graph,
            interval= 50,
            repeat=False)
        self.running = True
        self.ani._start()
        
    
    # Function to update the graph on GUI
    def update_graph(self, i):
        self.ax1.clear()
        self.ax1.set_xlabel("Displacement (mm)")
        self.ax1.set_ylabel("Force (N)")
        self.ax1.plot(self.disp_final, self.load_final, lw = 0.5, color="darkmagenta") # update graph


    # Start button function 
    def start_data(self):
        global state
        if state == True:
            # Starts serial reading and data transfer from serial class
            s.read_serial_start()
            s.serial_data()
            # Handles data with regard to test condition
            self.handle_data()
            #Checks every 0.1 second the state varialbe acts as while loop in tkinter
            root.after(100, self.start_data)
            # Sets displayed text 
            self.disp_text.set(self.disp)
            self.load_text.set(self.load)
        else:
            state = True
    
    #Stop button function 
    def stop_data(self):
        global state
        state = False

    # Tare disp button function 
    def tare_disp(self):
        value = (b"w%")
        s.send_serial_data(value)
    
    # Tare disp button function 
    def tare_load(self):
        self.x0 = 0
        list_x0 = []
    
        for i in range(0, 20):
            list_x0.append(s.data[1])
        self.x0 = np.mean(list_x0)

        self.zero_load = round(self.cal_b+(self.cal_factor* self.x0), 3)

        print(self.zero_load)


    # Aquire data function both starts live plot and records final data into two lists. 
    def aquire_data(self):
        if self.aquire == False:
            self.aquire = True  
            self.aquire_but.config(bg = "red")
            return self.start_ani()    
        else:
            self.aquire = False
            self.aquire_but.config(bg = "SystemButtonFace")

    # Function for clearing the data and plot
    def clear_all(self):

        # Clears plot 
        self.fig_1 = Figure(figsize=(7,4), dpi=100, tight_layout = True)
        self.ax1 = self.fig_1.add_subplot(111)
        self.ax1.set_xlabel("Displacement (mm)")
        self.ax1.set_ylabel("Force (N)")
        self.ax1.plot([],[])       
    
        self.canvas1 = FigureCanvasTkAgg(self.fig_1,master=self.master)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().grid(row=0,column=1,padx=5, pady = 5)

        # Clears data 
        self.disp_final = []
        self.load_final = []
    
    # Save function for aquired data
    def file_save(self):
        with open(filedialog.asksaveasfilename(defaultextension=".csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(zip(self.disp_final, self.load_final))


'''THE MAIN LOOP FOR THE GUI'''
# Main loop in the         
def main():
    #Main script
    global root
    root = tk.Tk()
    root.config(bg="#DCE4E6")
    root.title("Data Aquisition")

    app = App(root)

    # Kills the root and closes the serial connection 
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                global s
                s.close()
                root.destroy()
            except:
                root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == '__main__':
    main()