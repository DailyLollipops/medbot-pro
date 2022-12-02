#include <Stepper.h>

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
const int cuffStepperDirPin = 9;
const int cuffStepperStepPin = 10;
const int cuffStepperEnPin = 11;

// Global variables
String command = "";
int current_command = -1;
int sanitizerTime = 2000; //Sanitizer livetime in millis
bool fingerDetected = false;
bool armDetected = false;
bool oximeterLocked = false;
bool cuffLocked = false;
int oximeterStepperSteps = 200;
int roll = 0;
int armThreshold = 30;
int cuffThreshold = 100;

void setup() {
  // Initialize Sanitizer Components
  pinMode(sanitizerRelay, OUTPUT);

  // Initialize Oximeter Components
  pinMode(oximeterTouchSensor, INPUT);
  oximeterStepper.setSpeed(10);

  // Initialize BPM Components
  pinMode(armPiezo, INPUT);
  pinMode(cuffFSR, INPUT);
  pinMode(bpmSolenoid, OUTPUT);
  pinMode(cuffStepperEnPin, OUTPUT);
  pinMode(cuffStepperDirPin, OUTPUT);
  pinMode(cuffStepperStepPin, OUTPUT);
  digitalWrite(bpmSolenoid, HIGH);
  
  // Initialize serial
  Serial.begin(9600);
}

void loop() {
  if(command == "0"){
    current_command = 0;
    command = "";
  }
  else if(command == "1"){
    current_command = 1;
    command = "";
  }
  else if(command == "2"){
    current_command = 2;
    command = "";
  }
  else if(command == "3"){
    current_command = 3;
    command = "";
  }
  else if(command == "4"){
    current_command = 4;
    command = "";
  }
  else if(command == "9"){
    current_command = 9;
    command = "";
  }
  /* 
    Main Loop 
  */
  // Command selector
  if(current_command == -1){
    command = receiveCommand();
  }

  // Start body check
  else if(current_command == 0){
    if(!fingerDetected){
      detectFinger();
    }
    if(!armDetected){
      detectArm();
    }
    if(fingerDetected && armDetected){
      if(oximeterLocked && cuffLocked){
        sendResponse("0");
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

  // Stop body check or Body release
  else if(current_command == 1 || current_command == 2){
    oximeterRelease();
    cuffRelease();
    current_command = -1;
  }

  // Start sanitize
  else if(current_command == 3){
    sanitize();
    sendResponse("1");
    current_command = -1;
  }

  // Start Bpm
  else if(current_command == 4){
    startBPM();
    current_command = -1;
  }

  // Reset global variables
  else if(current_command == 9){
    reset();
    current_command = -1;
  }
}

void detectFinger(){
  /*
   * Detect finger on top of touch sensor
   * Returns '9' on Serial if True
   */
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH){
    fingerDetected = true;
    sendResponse("9");
  }
}

void detectArm(){
  /*
   * Detect if arm is inserted on BPM cuff
   * Returns '8' on Serial if True
   */
  int piezoValue = analogRead(armPiezo);
  if(piezoValue < armThreshold){
    armDetected = true;
    sendResponse("8");
  }
}

void oximeterLock(){
  /*
   * Locks the oximeter. 
   * Only locks if finger is on the oximeter and
   * oximeter is currently not locked
   */
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH && !oximeterLocked){
    oximeterStepper.step(oximeterStepperSteps);
    oximeterLocked = true;
  }
}

void oximeterRelease(){
  /*
   * Release the oximeter
   * Only releases if oximeter is currently locked 
   */
  if(oximeterLocked){
    oximeterStepper.step(-oximeterStepperSteps);    
  }
  oximeterLocked = false;    
}

void cuffLock(){
  /*
   * Tighten the arm cuff until it is tight
   * enough depending on the cuff Threshold value
   * Only tightens if cuff is currently locked
   */
  if(!cuffLocked){
    digitalWrite(cuffStepperDirPin, LOW);
    int fsrValue = analogRead(cuffFSR);
    while(fsrValue > cuffThreshold){
      for(int i = 0; i < 50; i++){
        digitalWrite(cuffStepperStepPin, HIGH);
        delayMicroseconds(15000);
        digitalWrite(cuffStepperStepPin, LOW);
        delayMicroseconds(15000); 
      }
      fsrValue = analogRead(cuffFSR);
      roll++;
    }
    cuffLocked = true;
  }
}

void cuffRelease(){
  /*
   * Release the cuff
   * Only release if cuff is currently locked
   */
  if(cuffLocked){
    digitalWrite(cuffStepperDirPin, HIGH);
    for(int i = 0; i < roll; i++){
      for(int j = 0; j < 50; j++){
        digitalWrite(cuffStepperStepPin, HIGH);
        delayMicroseconds(15000);
        digitalWrite(cuffStepperStepPin, LOW);
        delayMicroseconds(15000); 
      }
    }
    roll = 0;
    cuffLocked = false;
  }
}

void sanitize(){
  /*
   * Turn on sanitizer
   */
  digitalWrite(sanitizerRelay, HIGH);
  delay(1000);
  digitalWrite(sanitizerRelay, LOW);
  delay(sanitizerTime);
  digitalWrite(sanitizerRelay, HIGH);
  delay(1000);
  digitalWrite(sanitizerRelay, LOW);
  delay(1000);
  digitalWrite(sanitizerRelay, HIGH);
  delay(1000);
  digitalWrite(sanitizerRelay, LOW);
}

void startBPM(){
  /*
   * Turn on BPM
   */
  digitalWrite(bpmSolenoid, LOW);
  delay(250);
  digitalWrite(bpmSolenoid, HIGH);
  delay(1000);
}

void reset(){
  fingerDetected = false;
  armDetected = false;   
}
void sendResponse(String response){
  Serial.println(response);    
}

String receiveCommand(){
  if(!Serial.available()){
    String sent = Serial.readStringUntil('\n');
    if(sent != ""){
      Serial.println("ok");
      return sent;
    }
  }
}