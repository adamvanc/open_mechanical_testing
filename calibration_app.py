from curses import baudrate
import tkinter as tk
from turtle import color
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
from sklearn.metrics import r2_score

'''Class serial_data adapted from the code written 
by "The Poor Enginer" who does a very nice 
tutorial on how to use threading to continuously read serial using Pyserial at this website 
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
        self.isRun = True
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
        while (self.isRun):
            self.packet = self.serial_connect.readline().decode('utf').rstrip()
            self.is_receiving = True  

    # Process recieved data
    def serial_data(self):
            try:
                self.data =[float(i) for i in self.packet.split("\t")]
            except:
                self.data = [[],[]]
   

    # To allow the sending of serial data to the microcontroller
    def sendserial_data(self, data):
        self.serial_connect.write(data)

    # Close the serial connection   
    def close(self):
        self.isRun = False
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
        self.cal_data = [[],[],[],[]]
        self.cal_mean = {}

    
        # Frames 
        self.frame_bg1 = tk.Frame(master, bg="#DCE4E6")
        self.frame_bg1.grid(column = 0, row = 0,sticky = "NW")

        self.frame_1 = tk.LabelFrame(self.frame_bg1,  bg="#DCE4E6", text = "Connection",
        borderwidth=1, font="Helvetica 11 bold")
        self.frame_1.grid(column = 0, row = 0, sticky = "NW", padx = 10, pady = 10)

        self.frame_4 = tk.LabelFrame(self.frame_bg1, text = "Known Weights", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_4.grid(column = 0, row = 1, sticky = "NW", padx = 10, pady = 10)

        self.frame_3 = tk.LabelFrame(self.frame_bg1, text = "Select Weight", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_3.grid(column = 0, row = 2, sticky = "NW", padx = 10, pady = 10)

        self.frame_2 = tk.LabelFrame(self.frame_bg1, text = "Data Collection", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_2.grid(column = 0, row = 3, sticky = "NW", padx = 10, pady = 10)

        self.frame_5 = tk.LabelFrame(self.frame_bg1, text = "Save", 
        bg="#DCE4E6",borderwidth=1, font="Helvetica 11 bold")
        self.frame_5.grid(column = 0, row = 4, sticky = "NW", padx = 10, pady = 10)


        # Buttons for Serial connect
        self.com_label = tk.Label(self.frame_1, text = "Availible Ports",
        bg="#DCE4E6", font="Helvetica 8 bold")
        self.com_label.grid (column = 0, row = 0, padx = 2, pady = 10)

        self.refresh_but = tk.Button(self.frame_1, text = "Refresh", 
        height = 1, width = 8, command = self.refresh)
        self.refresh_but.grid(column = 2, row = 0, padx= 5, pady = 10)

        self.connect_but = tk.Button(self.frame_1, text = "Connect", 
        height = 1, width = 8, command = self.conntect)
        self.connect_but.grid(column = 0, row = 1, padx= 10, pady = 10)

        self.init_but = tk.Button(self.frame_1, text = "Initialize", 
        height = 1, width = 8, command = self.initialize)
        self.init_but.grid(column = 1, row = 1, padx= 10, pady = 10)

        self.connect_but = tk.Button(self.frame_1, text = "Disconect", 
        height = 1, width = 8, command = self.disconect)
        self.connect_but.grid(column = 2, row = 1, padx= 10, pady = 10)

        # Live readout 
        self.load_label = tk.Label(self.frame_1, text = "Load cell readout",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.load_label.grid (column = 0, row = 2, padx = 2, pady = 10)

        self.load_text = tk.StringVar()
        self.load_text.set("---")
        self.label = tk.Label(self.frame_1, textvariable=self.load_text,
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=1, row = 2, padx=10, pady=10)
                
        # Populate list with availible ports 
        self.ports = ser_list.comports()
        self.coms = [com[0] for com in self.ports]
        self.coms.insert(0, "-")

        # Selecting the COM drop button
        self.clicked_com = tk.StringVar()
        self.clicked_com.set(self.coms[0])
        self.drop_COM = tk.OptionMenu(self.frame_1, self.clicked_com, *self.coms)
        self.drop_COM.grid (column = 1, row = 0, padx= 2, pady = 5)

        # Plot
        # Plot 1 
        self.fig_1 = Figure(figsize=(7,4), dpi=100, tight_layout = True)
        self.ax1 = self.fig_1.add_subplot(111)
        self.ax1.set_xlabel("Load cell read out")
        self.ax1.set_ylabel("Known weight (N)")
        self.ax1.plot([],[])       
    
        self.canvas1 = FigureCanvasTkAgg(self.fig_1,master=master)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().grid(row=0,column=1,padx=5, pady = 5)

        # Known weights boxes and labels 

        # Weight 1
        self.com_label = tk.Label(self.frame_4, text = "Weight 1 ",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.com_label.grid (column = 0, row = 0, padx = 2, pady = 10)

        self.W1_box = tk.Text(self.frame_4, height = 1, width = 10)
        self.W1_box.grid(column = 1, row = 0, padx = 10, pady = 2, sticky = "W")
        self.W1_box.config(font = ("Arial", 12))

        self.W1_text = tk.StringVar()
        self.W1_text.set("---")
        self.label = tk.Label(self.frame_4, textvariable=self.W1_text, 
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=2, row = 0, padx=10, pady=10)

        # Weight 2
        self.com_label = tk.Label(self.frame_4, text = "Weight 2 ",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.com_label.grid (column = 0, row = 1, padx = 2, pady = 10)

        self.W2_box = tk.Text(self.frame_4, height = 1, width = 10)
        self.W2_box.grid(column = 1, row = 1, padx = 10, pady = 2, sticky = "W")
        self.W2_box.config(font = ("Arial", 12))

        self.W2_text = tk.StringVar()
        self.W2_text.set("---")
        self.label = tk.Label(self.frame_4, textvariable=self.W2_text, 
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=2, row = 1, padx=10, pady=10)

        # Weight 3
        self.com_label = tk.Label(self.frame_4, text = "Weight 3 ",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.com_label.grid (column = 0, row = 2, padx = 2, pady = 10)

        self.W3_box = tk.Text(self.frame_4, height = 1, width = 10)
        self.W3_box.grid(column = 1, row = 2, padx = 10, pady = 2, sticky = "W")
        self.W3_box.config(font = ("Arial", 12))

        self.W3_text = tk.StringVar()
        self.W3_text.set("---")
        self.label = tk.Label(self.frame_4, textvariable=self.W3_text, 
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=2, row = 2, padx=10, pady=10)

        # Weight 4
        self.com_label = tk.Label(self.frame_4, text = "Weight 4 ",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.com_label.grid (column = 0, row = 3, padx = 2, pady = 10)

        self.W4_box = tk.Text(self.frame_4, height = 1, width = 10)
        self.W4_box.grid(column = 1, row = 3, padx = 10, pady = 2, sticky = "W")
        self.W4_box.config(font = ("Arial", 12))

        self.W4_text = tk.StringVar()
        self.W4_text.set("---")
        self.label = tk.Label(self.frame_4, textvariable=self.W4_text, 
        bg='#fff', fg='#f00', font = 18)
        self.label.grid(column=2, row = 3, padx=10, pady=10)

        # Make text box list and stringvar lists
        self.text_box_list = [self.W1_box, self.W2_box, self.W3_box, self.W4_box]
        self.stringvar_list = [self.W1_text, self.W2_text, self.W3_text, self.W4_text]

        # Plot button
        self.start_but = tk.Button(self.frame_4, text = "Plot", 
        height = 1, width = 8, command = self.plot)
        self.start_but.grid(column = 0, row = 5, padx= 10, pady = 10)

        # Calibration display
        self.cal_label = tk.Label(self.frame_4, text = "Calibration factor",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.cal_label.grid (column = 1, row = 5, padx = 2, pady = 10)

        self.cal_text = tk.StringVar()
        self.cal_text.set("-------")
        self.label = tk.Label(self.frame_4, textvariable=self.cal_text, 
        bg='#fff', fg='#2b28af', font = 18)
        self.label.grid(column=2, row = 5, padx=10, pady=10)

        # R-squared display
        self.r2_label = tk.Label(self.frame_4, text = "R-squared",
        bg="#DCE4E6", font="Helvetica 10 bold")
        self.r2_label.grid (column = 3, row = 5, padx = 2, pady = 10)


        self.r2_text = tk.StringVar()
        self.r2_text.set("----")
        self.label = tk.Label(self.frame_4, textvariable=self.r2_text, 
        bg='#fff', fg='#2b28af', font = 18)
        self.label.grid(column=4, row = 5, padx=10, pady=10)


        # Known weight radio buttons  
        self.test_option = tk.IntVar() 

        self.rad_butt_1 = tk.Radiobutton(self.frame_3, text= "Weight 1", font='Helvetica 10 bold',
        variable= self.test_option, value = 0, bg="#DCE4E6")
        self.rad_butt_1.grid(column=1, row = 0, pady = 5, sticky = "W")

        self.rad_butt_2 = tk.Radiobutton(self.frame_3, text= "Weight 2", font='Helvetica 10 bold',
        variable= self.test_option, value = 1, bg="#DCE4E6")
        self.rad_butt_2.grid(column=2, row = 0, pady = 5, sticky = "W")

        self.rad_butt_3 = tk.Radiobutton(self.frame_3, text= "Weight 3", font='Helvetica 10 bold',
        variable= self.test_option, value = 2, bg="#DCE4E6")
        self.rad_butt_3.grid(column=3, row = 0, pady = 5, sticky = "W")

        self.rad_butt_4 = tk.Radiobutton(self.frame_3, text= "Weight 4", font='Helvetica 10 bold',
        variable= self.test_option, value = 3, bg="#DCE4E6")
        self.rad_butt_4.grid(column=4, row = 0, pady = 5, sticky = "W")

        # Buttons for calibration control
        # Start/Stop/Set
        self.aquire_but = tk.Button(self.frame_2, text = "Acquire data", 
        height = 1, width = 8, command = self.aquire_data)
        self.aquire_but.grid(column = 0, row = 0, padx= 10, pady = 10)

        self.set_but = tk.Button(self.frame_2, text = "Set", 
        height = 1, width = 8, command = self.set_data)
        self.set_but.grid(column = 1, row = 0, padx= 10, pady = 10)

        # Clear and save buttons 
        # Clear button
        self.clear = tk.Button(self.frame_5, text = "Clear Data", height = 1, width = 8, 
        command = self.clear_all)
        self.clear.grid(column = 0, row = 0, padx = 20, pady = 10)

        # Save button for data 
        self.save = tk.Button(self.frame_5, text = "Save Data", height = 1, width = 8, 
        command = self.save_data)
        self.save.grid(column = 1, row = 0, padx = 20, pady = 10)

        # Save button for calibration factor 
        self.saveCal = tk.Button(self.frame_5, text = "Save calibraton", height = 1, width = 8, 
        command = self.save_cal)
        self.saveCal.grid(column = 2, row = 0, padx = 20, pady = 10)

    '''FUNCTIONS TO MAKE THE GUI WORK'''
    # Function to refresh list of ports 
    def refresh(self):
        self.ports = ser_list.comports()
        self.coms.insert(0, "-")
        self.coms = [com[0] for com in self.ports]
        
        self.drop_COM = tk.OptionMenu(self.frame_1, self.clicked_com, *self.coms)
        self.drop_COM.grid (column = 1, row = 0, padx= 2, pady = 5)
        
    # Function to initiate the serial connection 
    def conntect(self):
        print(self.clicked_com.get())
        portName = self.clicked_com.get()
        baudRate = 9600
        global s
        s = serial_data(portName, baudRate)
        

    # Function to process data for calculating means 
    def handle_data(self):
        self.load = s.data[1]

        if self.aquire == True:
            self.load_final.append(self.load)
            print(self.load_final)

    # Function to close serial connection 
    def disconect(self):
        s.close()


    # Initialize button function 
    def initialize(self):
        global state
        
        if state == True:
            # Starts serial reading and data transfer from serial class
            s.read_serial_start()
            s.serial_data()
            # Sets off data handler 
            self.handle_data()
            #Checks every 0.1 second the state varialbe acts as while loop in tkinter
            root.after(100, self.initialize)
            # Sets displayed text 
            self.load_text.set(s.data[1])
        else:
            state = True
    
    # Aquire data function for capturing data for averages. 
    def aquire_data(self):
        if self.aquire == False:
            self.aquire = True  
            self.aquire_but.config(bg = "red") 
            #Rests the list for calculating the average
            self.load_final = []
              
        else:
            self.aquire = False
            self.aquire_but.config(bg = "SystemButtonFace")

    # Set data for analysis 
    def set_data(self):
        # Takes data from temp list and adds it to appropriate list of final averages 
        self.cal_data[self.test_option.get()] = self.load_final

        #Clears x_mean
        x_mean = 0
        # Create mean of load cell read out for a given weight 
        x_mean = np.mean(self.cal_data[self.test_option.get()])
        # Create dictionary of weight and mean so to avoid confusion
        self.cal_mean[self.test_option.get()] = x_mean
        # display the mean load cell read
        self.stringvar_list[self.test_option.get()].set(round(x_mean,3))

    # Function for ploting and getting calibration factor 
    def plot(self):
        # Create a list of known weights
        known_weights = []
        for box in self.text_box_list:
            known_weights.append(float(box.get('1.0', 'end')))
        # Create matrix to plot  
        self.plot_data = [[],[]]
        # Add data to that matrix 
        for i in range(0, len(self.cal_mean)):
            self.plot_data[0].append(self.cal_mean[i])
            self.plot_data[1].append(known_weights[i])
        # Use Numpy polyfit function to build 1D linear model of the two variables
        self.coef = np.polyfit(self.plot_data[0], self.plot_data[1],1)
        # Create points to draw the line for the graph 
        poly1d_fn = np.poly1d(self.coef)

        # Calculate R2
        self.R2 = r2_score(self.plot_data[1], poly1d_fn(self.plot_data[0]))
        
        # Set the stringvars for calibtion factor and r2
        self.cal_text.set(round(self.coef[0],8))
        self.r2_text.set(round(self.R2, 3))
      
        # Redraw plot with calibration data 
        self.fig_1 = Figure(figsize=(7,4), dpi=100, tight_layout = True)
        self.ax1 = self.fig_1.add_subplot(111)
        self.ax1.set_xlabel("Load cell readout")
        self.ax1.set_ylabel("Known weight (N)")
        self.ax1.plot(self.plot_data[0],self.plot_data[1], "or", self.plot_data[0], poly1d_fn(self.plot_data[0]), "--k" )   
    
        self.canvas1 = FigureCanvasTkAgg(self.fig_1,master=self.master)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().grid(row=0,column=1,padx=5, pady = 5)


    # Function for clearing the data and plot
    def clear_all(self):
        # Clears plot 
        self.fig_1 = Figure(figsize=(7,4), dpi=100, tight_layout = True)
        self.ax1 = self.fig_1.add_subplot(111)
        self.ax1.set_xlabel("Load cell readout")
        self.ax1.set_ylabel("Known weight (N)")
        self.ax1.plot([],[])       
    
        self.canvas1 = FigureCanvasTkAgg(self.fig_1,master=self.master)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().grid(row=0,column=1,padx=5, pady = 5)

        # Clears data 
        self.cal_data = [[],[],[],[]]
        self.cal_mean = {}
        for i in range(0, len(self.stringvar_list)):
            self.stringvar_list[i].set('---')
        
    
    # Save functions
    # For data that makes the average 
    def save_data(self):
        rows = zip(self.cal_data[0], self.cal_data[1], self.cal_data[2], self.cal_data[3])

        with open(filedialog.asksaveasfilename(defaultextension=".csv"), 'w',newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)

    #For calibration factor in text file 
    def save_cal(self):
        cal = [str(self.coef[0])]
        b = [str(self.coef[1])]
        with open(filedialog.asksaveasfilename(defaultextension=".txt"), 'w', newline='') as f:
            for c in cal:
                f.write(c)
            f.write(" ")
            for b in b:
                f.write(b)
            
'''THE MAIN LOOP FOR THE GUI'''

# Main loop in the         
def main():
    #Main script
    global root
    root = tk.Tk()
    root.config(bg="#DCE4E6")
    root.title("Load Cell Calibration")

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