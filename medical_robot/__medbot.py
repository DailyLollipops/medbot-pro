from .__user import User
from pyzbar.pyzbar import decode
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES
from base64 import b64encode
from base64 import b64decode
from escpos.printer import Usb
from datetime import datetime
# from .__max30102 import MAX30102
from .__bp3gy12n import Microlife_BTLE
from serial import Serial
import cv2
import numpy
from .__utility import *
import speech_recognition
import pyttsx3

__all__ = ['Medbot']

########################################################
#                      Main Class                      #
########################################################

# This class requires a Database object to be initialized
# Commented lines is due to this code is being tested on a Windows Machine
# Would later remove if ported on Raspberry Pi
class Medbot:

    def __init__(self, database):
        self.database = database
        self.__password = bytes('MedbotPRBPM' + '\0\0\0\0\0', 'utf-8')
        self.current_user = None,
        self.has_user = False
        self.qrcode_scanner = cv2.VideoCapture(0)
        # self.oximeter = MAX30102()
        self.blood_pressure_monitor  = Microlife_BTLE()
        self.recognizer = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone(device_index = 2)
        self.speaker = pyttsx3.init()
        # self.printer = Usb(0x28e9, 0x0289, 0, 0x81, 0x01)
        self.printer = None
        # self.arduino = Serial('/dev/ttyACM0', 9600, timeout = 1)
        self.arduino = None
        self.body_check_started = False
        self.body_check_in_progress = False
        self.body_check_completed = False
        self.current_reading = {
            'pulse_rate': None,
            'systolic': None,
            'diastolic': None,
            'blood_saturation': None
        }

    # Returns the decoded QR Code message
    def __decodeframe(self, image):
        trans_img = cv2.cvtColor(image,0)
        qrcode = decode(trans_img)
        for obj in qrcode:
            points = obj.polygon
            (x,y,w,h) = obj.rect
            pts = numpy.array(points, numpy.int32)
            pts = pts.reshape((-1, 1, 2))
            thickness = 2
            isClosed = True
            line_color = (0, 0, 255)
            cv2.polylines(image, [pts], isClosed, line_color, thickness)
            data = obj.data.decode("utf-8")
            return data

    # Generates an encrypted text from the user's ID and password
    def __encrypt(self, decrypted):
        cipher = AES.new(self.__password,AES.MODE_ECB)
        encrypted = b64encode(cipher.encrypt(pad(decrypted.encode(),16))).decode()
        return encrypted

    # Decrypts the decoded QR Code text that includes user's ID and password
    def __decrypt(self, encrypted):
        cipher = AES.new(self.__password, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(b64decode(encrypted.encode())),16).decode()
        return decrypted

    # Check if QR Code is a valid Medbot QR Code
    def __verify_qrcode(self, qrdata):
        if('Medbot' in qrdata):
            credentials = qrdata.split(':')
            id = credentials[1]
            password = credentials[2]
            return id, password
        else:
            raise Exception('QRCode is not a valid one')

    # Opens an OpenCV window and scans QR Code      
    def __scan_qrcode(self):
        while True:
            ret, frame = self.qrcode_scanner.read()
            encrypted_data = self.__decodeframe(frame)
            cv2.imshow('Image', frame)
            cv2.waitKey(1)
            if(encrypted_data != None):
                decrypted_data = self.__decrypt(encrypted_data)
                break
        cv2.destroyAllWindows()
        return decrypted_data

    # Sets the current user based on the credentials found on database
    # Return a User object upon success
    def login(self):
        qrdata = self.__scan_qrcode()
        id, password = self.__verify_qrcode(qrdata)
        user = User(id, password)
        success = self.database.verify(user)
        if(success):
            self.current_user = user
            self.has_user = True
            return user
        else:
            del user
            raise Exception('Invalid Credentials')

    # Clears the current user
    def logout(self):
        self.current_user.authenticated = False
        self.current_user = None
        self.has_user = False

    # Send command to the Arduino to start body check
    # Also includes the body lock operation invoked in the Arduino
    def start_body_check(self):
        command = 'Start Body Check'
        # self.arduino.write(command.encode())
        self.body_check_started = True
        self.body_check_in_progress = True

    # Constantly listen to Arduino to send a body check completed response
    def wait_body_check(self):
        if(self.body_check_in_progress):
            while(self.body_check_in_progress):
                if(self.arduino.inWaiting > 0):
                    response = self.arduino.readline()
                    if(response == 'Body Check Complete'):
                        self.body_check_started = False
                        self.body_check_in_progress = False
                        self.body_check_completed = True
                        return True
        else:
            raise Exception('Body check is not started')

    # Send command to the Arduino to immediately stop the body check
    def stop_body_check(self):
        command = 'Stop Body Check'
        self.arduino.write(command.encode())
        self.body_check_in_progress = False
    
    # Return the body check status
    def get_body_check_status(self):
        if(not self.body_check_started and not self.body_check_completed):
            return 'Not started'
        elif(self.body_check_in_progress):
            return 'Ongoing'
        elif(self.body_check_completed):
            return 'Completed'

    # Send command to the Arduino to commence body release operation
    # Only available if body check is completed
    def body_release(self):
        if(self.body_check_completed):
            command = 'Body Release'
            self.arduino.write(command.encode())
        else:
            raise Exception('Body check is not completed or not started yet')
    
    # Get the Arduino response if available
    # Possible response('Body Check Completed','Sanitize Completed,)
    def get_arduino_response(self):
        if(self.arduino.inWaiting > 0):
            response = self.arduino.readline()
            return response

    # Send command to arduino
    # Can be used to explicitly invoke Arduino operation without calling specific functions
    # Possible commands('Start Body Check','Stop Body Check', 'Start Sanitize', 'Body Release')
    def send_command(self, command):
        commands = ['Start Body Check', 'Stop Body Check', 'Start Sanitize', 'Body Release']
        if(command in commands):
            if(command == 'Start Body Check'):
                self.start_body_position_check()
            elif(command == 'Stop Body Check'):
                self.stop_body_position_check()
            elif(command == 'Body Release'):
                self.body_release()
            elif(command == 'Start Sanitize'):
                self.start_sanitizer()
        else:
            raise Exception('Unknown command')

    # Start the MAX30102 oximeter
    # This function gets 5 valid measurements and returns it's average
    # Returns and sets pulse rate and blood saturation
    def start_oximeter(self):
        average_pulse_rate = 120
        average_blood_saturation = 95
        # pulse_rate_samples = []
        # blood_saturation_samples = []
        # count = 0
        # while(True):
        #     red, ir = self.oximeter.read_sequential()
        #     pulse_rate, pulse_rate_valid, blood_saturation, blood_saturation_valid = utility.calc_hr_and_spo2(ir[:100], red[:100])
        #     if(pulse_rate_valid and blood_saturation_valid and count <= 10):
        #         pulse_rate_samples.append(pulse_rate)
        #         blood_saturation_samples.append(blood_saturation)
        #         count = count + 1
        #     if(count > 5):
        #         break
        # average_pulse_rate = sum(pulse_rate_samples)/len(pulse_rate_samples)
        # average_blood_saturation = sum(blood_saturation_samples)/len(blood_saturation_samples)
        self.current_reading['pulse_rate'] = average_pulse_rate
        self.current_reading['blood_saturation'] = average_blood_saturation
        return average_pulse_rate, average_blood_saturation

    # Send command to the Arduino to press the start button on the blood pressure monitor
    # It then fetches the last measurement
    # Returns and sets the systolic and diastolic
    # Note: if the you wants to get the pulse rate from the bpm, you need to comment out
    #       the pulse rate lines in start_oximeter to prevent possible conflicts
    def start_blood_pressure_monitor(self):
        # Add button press for blood_pressure_monitor
        # Then wait for some second to start BLE
        self.blood_pressure_monitor.bluetooth_communication(self.blood_pressure_monitor.patient_id_callback)
        latest_measurement = self.blood_pressure_monitor.get_measurements()[-1]
        systolic = latest_measurement[1]
        diastolic = latest_measurement[2]
        # pulse_rate = latest_measurement[3]
        self.current_reading['systolic'] = systolic
        self.current_reading['diastolic'] = diastolic
        # self.current_reading['pulse_rate'] = pulse_rate
        return systolic, diastolic
    
    # Saves current reading to the database
    def save_reading(self,pulse_rate, systolic, diastolic, blood_saturation):
        blood_pressure = diastolic + ((systolic - diastolic)/3)
        now = datetime.now()
        date_now = now.strftime('%Y-%m-%d %H:%M:%S')
        values = (self.current_user.id,pulse_rate, blood_saturation, blood_pressure, systolic, diastolic, date_now, date_now)
        self.database.insert_record('readings', values)

    # Print some text on the thermal printer
    # Can pass in settings kwargs to define the settings for the thermal printer
    # Refer to the escpos documentation for this
    def print_results(self, content, **settings):
        self.printer.set(settings)
        success = False
        while(not success):
            if(self.printer.is_online()):
                if(self.printer.paper_status() != 0):
                    try:
                        self.printer.text(content)
                        self.printer.cut()
                        success = True
                    except:
                        break
                else:
                    raise Exception('No paper found')
            else:
                pass
        return success

    # Decodes and return speech from the microphone to text
    def get_voice_input(self, *accepted_answers):
        while(True):
            try:
                with self.microphone:
                    self.recognizer.adjust_for_ambient_noise(self.microphone, duration = 1)
                    audio = self.recognizer.listen(self.microphone)
                    text = self.recognizer.recognize_google(audio)
                    text = text.lower()
                    if(len(accepted_answers) > 0):
                        if(text in accepted_answers):
                            break
                    else:
                        break
            except self.recognizer.RequestErrorr:
                print('Cannot process request now')
            except self.recognizer.ValueError:
                print('Value error occured')
        return text
    
    # Convert text to speech
    def speak(self, text):
        self.speaker.say(text)
        self.speaker.runAndWait()

    # Set the speaker properties to change voice, rate or volume
    # Voice option can only be 'male' or 'female' and defaults to 'male'
    def set_speaker_properties(self, rate=100, volume=1.0, voice='male'):
        self.speaker.setProperty('rate', rate)
        self.speaker.setProperty('volume', volume)
        voices = self.speaker.getProperty('voices')
        if(voice == 'female'):
            self.speaker.setProperty('voice', voices[1].id)
        else:
            self.speaker.setProperty('voice', voices[0].id)

    # Send command to the Arduino to start sanitizing operation
    def start_sanitizer(self):
        command = 'Start Sanitizer'
        self.arduino.write(command.encode())

    # Returns a User object from the current user
    def get_current_user(self):
        try:
            if(self.current_user[0] is None):
                return None
        except:
            return self.current_user

    # Return a dictionary of current readings
    def get_current_reading(self):
        return self.current_reading

    # Returns an int(pulse rate)
    def get_current_pulse_rate(self):
        return self.current_reading['pulse_rate']

    # Returns an int(systolic)    
    def get_current_systolic(self):
        return self.current_reading['systolic']

    # Returns an int(diastolic)
    def get_current_diastolic(self):
        return self.current_reading['diastolic']

    # Returns an int(blood saturation)
    def get_current_blood_saturation(self):
        return self.current_reading['blood_saturation']

    ########################################################
    #              Tkinter Support Functions               #
    ########################################################

    # Essential functions that remove the looping to prevent blocking on GUIs

    # returns an image frame from an OpenCV instance
    def get_qrcode_scanner_frame(self):
        if self.qrcode_scanner.isOpened():
            ret, frame = self.qrcode_scanner.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    # Login user from a frame object
    def login_tk(self, frame):
        encrypted_data = self.__decodeframe(frame)
        decrypted_data = ''
        if(encrypted_data != None):
            decrypted_data = self.__decrypt(encrypted_data)
            id, password = self.__verify_qrcode(decrypted_data)
            user = User(id, password)
            success = self.database.verify(user)
            if(success):
                self.current_user = user
                self.has_user = True
                return True
            else:
                del user
                raise Exception('Invalid Credentials')

    ########################################################
    #                  Debugging Functions                 #
    ########################################################

    # Forcefully invoke body check as completed
    def body_check_complete(self):
        self.body_check_completed = True
        self.body_check_in_progress = False