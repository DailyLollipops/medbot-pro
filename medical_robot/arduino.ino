#include <Stepper.h>
#include <Servo.h>

// Sanitize components pinout
const int sanitizerRelay = 5;

// Oximeter components pinout
Servo oximeterServo;
const int oximeterServoPin = 6;
const int oximeterTouchSensor = 7;

// Blood Pressure Monitor components pinout
const int stepsPerRevolution = 2038;
Stepper cuffStepper = Stepper(stepsPerRevolution, 8, 10, 9, 11);
const int cuffPiezo = 12;
const int bpmSolenoid = 13;

// Global variables
int current_command = -1;
int sanitizerTime = 2000; //Sanitizer livetime in millis
bool oximeterLocked = false;
int piezoThreshold = 180;
bool cuffLocked = false;
int roll = 0;
int motorState = 0;
const int cuffThreshold = 180;

void setup() {
  // Initialize Sanitizer Components
  pinMode(sanitizerRelay, OUTPUT);

  // Initialize Oximeter Components
  oximeterServo.attach(oximeterServoPin);
  oximeterServo.write(135);
  pinMode(oximeterTouchSensor, INPUT);
  pinMode(cuffPiezo, INPUT);
  pinMode(bpmSolenoid, OUTPUT);
  cuffStepper.setSpeed(20);
}

void loop() {
  // command selector
  String command = receiveCommand();
  if(command != ""){
    if(command == "0"){
      current_command = 0; 
    }
    else if(command == "1"){
      current_command = 1;
    }
    else if(command == "2"){
      current_command = 2;
    }
    else if(command == "3"){
      current_command = 3;
    }
  }

  /* 
    Main Loop 
  */

  // Start body check
  if(command == 0){
    if(oximeterLocked && cuffLocked){
      command = -1;
    }
    oximeterLock();
    cuffLock();
  }

  // Stop body check or Body release
  else if(command == 1 || command == 2){
    oximeterRelease();
    cuffRelease();
    command = -1;
  }

  // Start sanitize
  else if(command == 3){
    sanitize();
    command = -1;
  }
}

void oximeterLock(){
  int touchSensorValue = digitalRead(oximeterTouchSensor);
  if(touchSensorValue == HIGH && !oximeterLocked){
    oximeterServo.write(-90);
    oximeterLocked = true;
  }
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

void oximeterRelease(){
  if(oximeterLocked){
    oximeterServo.write(135);    
  }
  oximeterLocked = false;    
}

void cuffLock(){
  int piezoValue = analogRead(cuffPiezo);
  if(!cuffLocked){
    if(piezoValue < piezoThreshold){
      cuffStepper.step(-stepsPerRevolution);
      piezoValue = analogRead(cuffPiezo);
      roll++;
    }
    else{
      cuffLocked = true;
    }    
  }
}

void cuffRelease(){
  if(roll > 0){
    for(int i = 0; i < roll; i++){
      cuffStepper.step(stepsPerRevolution);
    }
    roll = 0;
  }
  cuffLocked = false;
}

void sendResponse(String response){
  Serial.println(response);    
}

String receiveCommand(){
  if(!Serial.available()){
    String command = Serial.readString();
    return command;        
  }
  else{
    return "";
  } 
}