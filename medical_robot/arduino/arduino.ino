#include <Stepper.h>

/*
 * Available commands
 * 0 - Start body check 
 * 1 - Stop body check
 * 2 - Stop body check
 * 3 - Start sanitizer
 * 4 - Start BPM
 * 5 - Detect arm
 * 6 - Detect arm loop
 * 7 - Detect finger
 * 8 - Detect finger loop
 * 9 - Reset
 * 10 - Forward oximeter stepper (DEBUG)
 * 11 - Backward oximeter stepper (DEBUG)
 * 12 - Forward cuff stepper (DEBUG)
 * 13 - Backward cuff stepper (DEBUG)
 * 14 - Oximeter lock
 * 15 - Oximeter release
 * 16 - Cuff lock
 * 17 - cuff release
 * 
 * Responses
 * 90 - False
 * 91 - True
 * 92 - Operation Completed
 * 93 - Operation Interrupted
 * 94 - Arm Detected
 * 95 - Finger Detected
 */
 
// Sanitize components pinout
const int sanitizerRelay = 2;

// Oximeter components pinout
const int stepsPerRevolution = 2038;
Stepper oximeterStepper = Stepper(stepsPerRevolution, 3, 5, 4, 6);
const int oximeterTouchSensor = 7;

// Blood Pressure Monitor components pinout
const int armPiezo = A0;
const int cuffFSR = A1;
const int bpmSolenoid = 8;
const int forwardButton = 9;
const int reverseButton = 10;
const int armSensor = 11;
const int cuffMotorIn1Pin = 12;
const int cuffMotorIn2Pin = 13;

// Global variables
String command = "";
int current_command = -1;
int sanitizerTime = 4000; //Sanitizer livetime in millis
bool fingerDetected = false;
bool armDetected = false;
bool oximeterLocked = false;
bool cuffLocked = false;
long int cuffActiveMillis = 0;
int oximeterStepperSteps = 750;
int armThreshold = 30;
int cuffThreshold = 600;

void setup() {
  // Initialize Sanitizer Components
  pinMode(sanitizerRelay, OUTPUT);

  // Initialize Oximeter Components
  pinMode(oximeterTouchSensor, INPUT);
  oximeterStepper.setSpeed(10);

  // Initialize BPM Components
  pinMode(armPiezo, INPUT);
  pinMode(cuffFSR, INPUT);
  pinMode(armSensor, INPUT);
  pinMode(bpmSolenoid, OUTPUT);
  pinMode(cuffMotorIn1Pin, OUTPUT);
  pinMode(cuffMotorIn2Pin, OUTPUT);
  digitalWrite(bpmSolenoid, HIGH);
  digitalWrite(cuffMotorIn1Pin, LOW);
  digitalWrite(cuffMotorIn2Pin, LOW);

  // Initialize Buttons
  pinMode(forwardButton, INPUT_PULLUP);
  pinMode(reverseButton, INPUT_PULLUP);
  
  // Initialize serial
  Serial.begin(9600);
}

void loop() {
  /* 
    Main Loop 
  */
  
  // Check forwardButtonState
  int forwardButtonValue = digitalRead(forwardButton);
  if(forwardButtonValue == LOW){
    cuffMotorForward();
  }
  
  // Check reverseButtonState
  int reverseButtonValue = digitalRead(reverseButton);
  if(reverseButtonValue == LOW){
    cuffMotorBackward();  
  }
  
  // Command selector
  if(current_command == -1){
    receiveCommand();
  }

  // Start body check
  else if(current_command == 0){
    startBodyCheck();
    current_command = -1;
  }

  // Stop body check or Body release
  else if(current_command == 1 || current_command == 2){
    oximeterRelease();
    cuffRelease();
    current_command = -1;
  }

  // Start sanitizer
  else if(current_command == 3){
    sanitize();
    current_command = -1;
  }

  // Start BPM
  else if(current_command == 4){
    startBPM();
    current_command = -1;
  }

  // Detect Arm
  else if(current_command == 5){
    detectArm();
    current_command = -1;
  }

  // Detect Arm Loop
  else if(current_command == 6){
    detectArmLoop();
    current_command = -1;
  }
  
  // Detect Finger
  else if(current_command == 7){
    detectFinger();
    current_command = -1;
  }

  // Detect Finger
  else if(current_command == 8){
    detectFingerLoop();
    current_command = -1;
  }
  
  // Reset global variables
  else if(current_command == 9){
    reset();
    current_command = -1;
  }

  // Forward Oximeter Stepper
  else if(current_command == 10){
    oximeterStepperForward();
    current_command = -1;
  }

  // Reverse Oximeter Stepper
  else if(current_command == 11){
    oximeterStepperBackward();
    current_command = -1;
  }

  // Forward Cuff Stepper
  else if(current_command == 12){
    cuffMotorForward();
    current_command = -1;
  }

  // Reverse Cuff Stepper
  else if(current_command == 13){
    cuffMotorBackward();
    current_command = -1;
  }

  // Oximeter Lock
  else if(current_command == 14){
    oximeterLock();
    current_command = -1;
  }

  // Oximeter Release
  else if(current_command == 15){
    oximeterRelease();
    current_command = -1;
  }

  // Cuff Lock
  else if(current_command == 16){
    cuffLock();
    current_command = -1;
  }

  // Cuff Release
  else if(current_command == 17){
    cuffRelease();
    current_command = -1;
  }
}

void detectArm(){
  /*
   * Detect if arm is inserted on BPM cuff
   * Returns '94' on Serial if True
   * otherwise returns '0'
   */
  int armSensorValue = digitalRead(armSensor);
  if(armSensorValue == HIGH){
    armDetected = true;
    sendResponse("94");
  }
  else{
    armDetected = false;
    sendResponse("90");
  }
}

void detectArmLoop(){
  /*
   * Continously detect if arm is placed on
   * cuff. Always return '94'  on Serial
   */
  while(!armDetected){
    int armSensorValue = digitalRead(armSensor);
    if(armSensorValue == HIGH){
      armDetected = true;
      sendResponse("94");
    }
  }
}

void detectFinger(){
  /*
   * Detect finger on top of touch sensor
   * Returns '95' on Serial if True otherwise
   * returns '0'
   */
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH){
    fingerDetected = true;
    sendResponse("95");
  }
  else{
    fingerDetected = false;
    sendResponse("90");
  }
}

void detectFingerLoop(){
  /*
   * Continouosly detect if finger is in
   * the oximeter. Always return '95' on Serial
   */
  while(!fingerDetected){
    int value = digitalRead(oximeterTouchSensor);
    if(value == HIGH){
      fingerDetected = true;
      sendResponse("95");
    }
  }
}

void startBodyCheck(){
  /*
   * Start detecting arm and finger
   * Also starts locking operation
   * when detected
   */
  if(!fingerDetected){
    detectFinger();
  }
  if(!armDetected){
    detectArm();
  }
  if(fingerDetected && armDetected){
    if(oximeterLocked && cuffLocked){
      sendResponse("92");
      current_command = -1;
    }
    else if(!oximeterLocked){
      oximeterLock();
    }
    else if(!cuffLocked){
      cuffLock();
    }
  }  
}

void oximeterLock(){
  /*
   * Locks the oximeter. 
   * Only locks if oximeter is currently 
   * not locked
   */
  if(!oximeterLocked){
    oximeterStepper.step(-oximeterStepperSteps);
    oximeterLocked = true;
  }
  sendResponse("92");
}

void oximeterRelease(){
  /*
   * Release the oximeter
   * Only releases if oximeter is currently locked 
   */
  if(oximeterLocked){
    oximeterStepper.step(oximeterStepperSteps);
    oximeterLocked = false;    
  }
  sendResponse("92");
}

void cuffLock(){
  /*
   * Tighten the arm cuff until it is tight
   * enough depending on the cuff Threshold value
   * Only tightens if cuff is currently not locked
   */
  bool interrupted = false;
  if(!cuffLocked){
    int fsrValue = analogRead(cuffFSR);
    long int startMillis = millis();
    while(fsrValue < cuffThreshold){
      digitalWrite(cuffMotorIn1Pin, HIGH);
      digitalWrite(cuffMotorIn2Pin, LOW);
      int stopButtonValue = digitalRead(forwardButton);
      int okButtonValue = digitalRead(reverseButton);
      if(stopButtonValue == LOW){
        long int endMicros = millis();
        cuffActiveMillis = endMicros - startMillis;
        interrupted = true;
        break;
      }
      if(okButtonValue == LOW){
        cuffActiveMillis = 0;
        break;
      }
      fsrValue = analogRead(cuffFSR);
    }
    digitalWrite(cuffMotorIn1Pin, LOW);
    digitalWrite(cuffMotorIn2Pin, LOW);
    if(interrupted){
      sendResponse("93");
      startMillis = millis();
      if(cuffActiveMillis < 2000){
        while(1){
          long int currentMillis = millis() - startMillis;
          digitalWrite(cuffMotorIn1Pin, LOW);
          digitalWrite(cuffMotorIn2Pin, HIGH);
          if(currentMillis >= cuffActiveMillis){
            break;
          }         
        } 
      }
      else{
        digitalWrite(cuffMotorIn1Pin, LOW);
        digitalWrite(cuffMotorIn2Pin, HIGH);
        delay(2000);       
      }
      digitalWrite(cuffMotorIn1Pin, LOW);
      digitalWrite(cuffMotorIn2Pin, LOW);
    }
    else{
      cuffLocked = true;
      sendResponse("92"); 
    }
  }
  else{
   sendResponse("92"); 
  }
}

void cuffRelease(){
  /*
   * Release the cuff
   * Only release if cuff is currently locked
   */
  if(cuffLocked){
    digitalWrite(cuffMotorIn1Pin, LOW);
    digitalWrite(cuffMotorIn2Pin, HIGH);
    delay(2000);
    digitalWrite(cuffMotorIn1Pin, LOW);
    digitalWrite(cuffMotorIn2Pin, LOW);
    cuffLocked = false;
  }
  sendResponse("92");
}

void sanitize(){
  /*
   * Turn on sanitizer
   */
  digitalWrite(sanitizerRelay, HIGH);
  delay(500);
  digitalWrite(sanitizerRelay, LOW);
  delay(500);
  digitalWrite(sanitizerRelay, HIGH);
  delay(500);
  digitalWrite(sanitizerRelay, LOW);
  delay(sanitizerTime);
  digitalWrite(sanitizerRelay, HIGH);
  delay(500);
  digitalWrite(sanitizerRelay, LOW);
  sendResponse("92");
}

void startBPM(){
  /*
   * Turn on BPM
   */
  digitalWrite(bpmSolenoid, LOW);
  delay(250);
  digitalWrite(bpmSolenoid, HIGH);
  delay(1000);
  sendResponse("92");
}

void reset(){
  /*
   * Reset back to default state
   * Invoked when resetting the unit with
   * medbot.reset()
   */
  
  fingerDetected = false;
  armDetected = false;
  if(oximeterLocked){
    oximeterStepper.step(oximeterStepperSteps);
    oximeterLocked = false;    
  }
  if(cuffLocked){
    digitalWrite(cuffMotorIn1Pin, LOW);
    digitalWrite(cuffMotorIn2Pin, HIGH);
    delay(2000);
    digitalWrite(cuffMotorIn1Pin, LOW);
    digitalWrite(cuffMotorIn2Pin, LOW);
    cuffLocked = false;
  }
  sendResponse("92");
}

void sendResponse(String response){
  /*
   * Send response to the Raspberry Pi
   */
  Serial.println(response);    
}

void receiveCommand(){
  /*
   * Get and return command from Raspberry Pi
   */
  if(Serial.available()){
    int sent = Serial.readStringUntil('\n').toInt();
    Serial.println("ok");
    current_command = sent;
  }
}

/*
 * Debug Functions
 */
void oximeterStepperForward(){
  /*
   * Attempt to move the oximeter's stepper
   * motor forward by 100 steps and perform
   * oximeter lock bypassing the touch sensor value
   */
  oximeterStepper.step(100);
}

void oximeterStepperBackward(){
  /*
   * Move the oximeter's stepper motor backward
   * by 100 steps to perform oximeter release
   * function
   */
  oximeterStepper.step(-100);
}

void cuffMotorForward(){
  /*
   * Attempt to move the cuff's motor
   * to perform cuff locking operation bypassing
   * the FSR value
   */
  digitalWrite(cuffMotorIn1Pin, HIGH);
  digitalWrite(cuffMotorIn2Pin, LOW);
  delay(500);
  digitalWrite(cuffMotorIn1Pin, LOW);
  digitalWrite(cuffMotorIn2Pin, LOW);
}

void cuffMotorBackward(){
  /*
   * Move the cuff's motor backward releasing
   * the cuff
   */
  digitalWrite(cuffMotorIn1Pin, LOW);
  digitalWrite(cuffMotorIn2Pin, HIGH);
  delay(500);
  digitalWrite(cuffMotorIn1Pin, LOW);
  digitalWrite(cuffMotorIn2Pin, LOW);
}