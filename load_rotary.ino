#include "Q2HX711.h" // Library for the load cell

//Library for the HX711 is provided Scott Russell under the standart MIT license 
/*
MIT License

Copyright (c) Scott Russell 2015

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*/

#include "RotaryEncoder.h" //Library used for Rotory Encoder

// Library for the rotary encoder was provided Matthias Hertel under Licence by Mattias Hertle 
/*
  Copyright (c) 2005-2012 by Matthias Hertel, http://www.mathertel.de/

  All rights reserved.

  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the copyright owners nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

//Load cell definition 
Q2HX711 hx711(hx711_data_pin, hx711_clock_pin);

//Rotoary Encoder definition 
RotaryEncoder encoder(A2, A3);


//gloabal varialbes for the rotory encoder 
static int pos = 0;
float measure = 0.000;
int newPos = 0;


//global variables for the CheckIF function 
char receivedCommand;
bool newData = false;
bool enableRun = true;


//global variables for the sudo time stamp. 
int counter = 0;
float timet = 0.1;
float timer = 0.0;
float newTime = 0.0;
float useTime = 0.0;
int cycles =0;






void setup() {
  Serial.begin(9600);

  //Code snippit for the interrupt pins and IRS was provided Matthias Hertel (http://www.mathertel.de/Arduino/RotaryEncoderLibrary.aspx)

  //For the rotorary encoder you must define the pin interupts. The Arduino environment has no direct support for these itterupts so you must programme an
  //Iterup Service Routine (ISR).

  PCICR |= (1 << PCIE1);    // This enables Pin Change Interrupt 1 that covers the Analog input pins or Port C.
  PCMSK1 |= (1 << PCINT10) | (1 << PCINT11);  // This enables the interrupt for pin 2 and 3 of Port C.

  // The Interrupt Service Routine for Pin Change Interrupt 1
  // This routine will only be called on any signal change on A2 and A3: exactly where we need to check.
}


// This is what runs when the pin interiupr happens 
ISR(PCINT1_vect) {
  encoder.tick(); // just call tick() to check the state.

}

void loop() 
{

 checkSerial(); //check if statements for computer control 
 sendFormattedData(); //function for sending formatted data
 encode();
}




void encode()
{
  newPos = encoder.getPosition(); // Get absolute encoder position 
  measure = (0.001*newPos); // Convert the absolute position to a measurment based on the thread size of testing machine 
  if (pos != newPos) 
  {
    pos = newPos;
  }

}

void checkSerial() //Checking the serial port via IF statements
{
  if (Serial.available() > 0) //Check if there is incoming from the serial port.
  {    
    receivedCommand = Serial.read(); // This will read the command character sent from the computer 
    newData = true; // A bollean turns to true to indicate that new data is being recieved 
  }
 
  if (newData == true) 
  {
    //Comands for starting and stoping data 
    if (receivedCommand == 'd') //Sending formatted data
    {
      enableRun = true; //This enables the function for sending formatted data
    }
 
   
    if (receivedCommand == 's') //Immediately stops the code
    {
      
      enableRun = false;
    }
 


    
  if (receivedCommand == 'w') //Tares the zero position of the rotary encoder 
    {
    encoder.setPosition(0);
    delay(500);
    }
 }
}

void sendFormattedData()// Creating the series of data which will be transferred to the serial terminal formatted
{

  if (enableRun == true)
  {
    
    useTime = (newTime +(0.1*cycles)); // A time code created by the 10Hz sample frequenct of the HX711
    
    Serial.print(measure,4); //rotary encoder output

    Serial.print('\t'); //separate it with a tab
 
    Serial.println(hx711.read()); //new line

    
    cycles++;
 
  }  
  
}

   
