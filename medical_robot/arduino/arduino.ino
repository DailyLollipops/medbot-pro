#include <Stepper.h>
#include <Servo.h>

// Sanitize components pinout
const int sanitizerRelay = 2;

// Oximeter components pinout
const int stepsPerRevolution = 2038;
Stepper oximeterStepper = Stepper(stepsPerRevolution, 3, 5, 4, 6);
const int oximeterTouchSensor = 7;

// Blood Pressure Monitor components pinout
const int cuffPiezo = A0;
const int armPiezo = A1;
const int bpmSolenoid = 8;
const int cuffStepperEnPin = 9;
const int cuffStepperDirPin = 10;
const int cuffStepperStepPin = 11;

// Global variables
String command = "";
int current_command = -1;
int sanitizerTime = 2000; //Sanitizer livetime in millis
bool fingerDetected = false;
bool armDetected = true;
bool oximeterLocked = false;
bool cuffLocked = false;
int oximeterStepperSteps = 200;
int roll = 0;
int motorState = 0;
int armThreshold = 30;
int cuffThreshold = 100;

void setup() {
  // Initialize Sanitizer Components
  pinMode(sanitizerRelay, OUTPUT);

  // Initialize Oximeter Components
  pinMode(oximeterTouchSensor, INPUT);
  oximeterStepper.setSpeed(10);

  // Initialize BPM Components
  pinMode(cuffPiezo, INPUT);
  pinMode(armPiezo, INPUT);
  pinMode(bpmSolenoid, OUTPUT);
  pinMode(cuffStepperEnPin, OUTPUT);
  pinMode(cuffStepperDirPin, OUTPUT);
  pinMode(cuffStepperStepPin, OUTPUT);

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
  else if(current_command == 9){
    startBPM();
    current_command = -1;
  }
}

void detectFinger(){
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH){
    fingerDetected = true;
    sendResponse("9");
  }
}

void detectArm(){
  int piezoValue = analogRead(armPiezo);
  if(piezoValue < armThreshold){
    armDetected = true;
    sendResponse("8");
  }
}

void oximeterLock(){
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH && !oximeterLocked){
    oximeterStepper.step(oximeterStepperSteps);
    oximeterLocked = true;
  }
}

void oximeterRelease(){
  if(oximeterLocked){
    oximeterStepper.step(-oximeterStepperSteps);    
  }
  oximeterLocked = false;    
}

void cuffLock(){
  if(!cuffLocked){
    digitalWrite(cuffStepperDirPin, LOW);
    int piezoValue = analogRead(cuffPiezo);
    while(piezoValue > cuffThreshold){
      digitalWrite(cuffStepperStepPin, HIGH);
      delayMicroseconds(2000);
      digitalWrite(cuffStepperStepPin, LOW);
      delayMicroseconds(2000);
      roll++;
    }
    cuffLocked = true;
  }
}

void cuffRelease(){
  if(roll > 0){
    digitalWrite(cuffStepperDirPin, HIGH);
    for(int i = 0; i < roll; i++){
      digitalWrite(cuffStepperStepPin, HIGH);
      delayMicroseconds(2000);
      digitalWrite(cuffStepperStepPin, LOW);
      delayMicroseconds(2000);cuffStepper.step(stepsPerRevolution);
    }
    roll = 0;
  }
  cuffLocked = false;
}

void sanitize(){
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
  digitalWrite(bpmSolenoid, HIGH);
  delay(250);
  digitalWrite(bpmSolenoid, LOW);
  delay(1000);
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