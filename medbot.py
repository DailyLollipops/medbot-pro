from random import randint
from user import User
from pyzbar.pyzbar import decode
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from base64 import b64encode,b64decode
from escpos.printer import Usb
from datetime import datetime
from bp3gy12n import Microlife_BTLE
import cv2
import numpy as np
# import max30102
# import hrcalc
import speech_recognition
import pyttsx3
import serial
import sqlite3

class Medbot:
    def __init__(self, database):
        self.database = database
        self.__password = bytes('MedbotPRBPM' + '\0\0\0\0\0', 'utf-8')
        self.current_user = None,
        self.has_user = False
        self.qrcode_scanner = cv2.VideoCapture(0)
        # self.oximeter = max30102.MAX30102()
        self.blood_pressure_monitor  = Microlife_BTLE()
        self.recognizer = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone(device_index = 2)
        self.speaker = pyttsx3.init()
        # self.printer = Usb(0x28e9, 0x0289, 0, 0x81, 0x01)
        self.printer = None
        # self.arduino = serial.Serial('/dev/ttyACM0', 9600, timeout = 1)
        self.arduino = None
        self.body_check_started = False
        self.body_check_in_progress = False
        self.body_check_completed = False
        self.latest_reading = {
            'pulse_rate': None,
            'systolic': None,
            'diastolic': None,
            'blood_saturation': None
        }

    def __decode(self, image):
        trans_img = cv2.cvtColor(image,0)
        qrcode = decode(trans_img)
        for obj in qrcode:
            points = obj.polygon
            (x,y,w,h) = obj.rect
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            thickness = 2
            isClosed = True
            line_color = (0, 0, 255)
            cv2.polylines(image, [pts], isClosed, line_color, thickness)
            data = obj.data.decode("utf-8")
            return data

    def __encrypt(self, decrypted):
        cipher = AES.new(self.__password,AES.MODE_ECB)
        encrypted = b64encode(cipher.encrypt(pad(decrypted.encode(),16))).decode()
        return encrypted

    def __decrypt(self, encrypted):
        cipher = AES.new(self.__password, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(b64decode(encrypted.encode())),16).decode()
        return decrypted

    def __verify_qrcode(self, qrdata):
        if('Medbot' in qrdata):
            credentials = qrdata.split(':')
            id = credentials[1]
            password = credentials[2]
            return id, password
        else:
            raise Exception('QRCode is not a valid one')

    def __scan_qrcode(self):
        while True:
            ret, frame = self.qrcode_scanner.read()
            encrypted_data = self.__decode(frame)
            cv2.imshow('Image', frame)
            cv2.waitKey(1)
            if(encrypted_data != None):
                decrypted_data = self.__decrypt(encrypted_data)
                break
        cv2.destroyAllWindows()
        return decrypted_data
                
    def login(self):
        qrdata = self.__scan_qrcode()
        id, password = self.__verify_qrcode(qrdata)
        user = User(id, password)
        success = self.database.verify(user)
        if(success):
            user.authenticated = True
            self.current_user = user
            self.has_user = True
            return user
        else:
            del user
            raise Exception('Invalid Credentials')

    # For GUI 
    def get_qrcode_scanner_frame(self):
        if self.qrcode_scanner.isOpened():
            ret, frame = self.qrcode_scanner.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def login_tk(self, frame):
        encrypted_data = self.__decode(frame)
        decrypted_data = ''
        if(encrypted_data != None):
            decrypted_data = self.__decrypt(encrypted_data)
            id, password = self.__verify_qrcode(decrypted_data)
            user = User(id, password)
            success = self.database.verify(user)
            if(success):
                user.authenticated = True
                self.current_user = user
                self.has_user = True
                return True
            else:
                del user
                raise Exception('Invalid Credentials')

    def logout(self):
        self.current_user.authenticated = False
        self.current_user = None
        self.has_user = False

    def start_body_position_check(self):
        command = 'Start Body Position Check'
        self.arduino.write(command.encode())
        self.body_check_started = True
        self.body_check_in_progress = True

    def wait_body_position_check(self):
        if(self.body_check_in_progress):
            while(self.body_check_in_progress):
                if(self.arduino.inWaiting > 0):
                    response = self.arduino.readline()
                    if(response == 'Body Position Check Complete'):
                        self.body_check_started = False
                        self.body_check_in_progress = False
                        self.body_check_completed = True
                        return True
                    else:
                        return response
        else:
            raise Exception('Body check is not started')

    def stop_body_position_check(self):
        command = 'Stop Body Position Check'
        self.arduino.write(command.encode())
        self.body_check_in_progress = False
    
    def get_body_position_check_status(self):
        return self.body_check_in_progress

    def body_release(self):
        command = 'Body Release'
        self.arduino.write(command.encode())
        
    def get_arduino_response(self):
        # Possible response('Body Position Check Completed','Sanitize Completed,)
        if(self.arduino.inWaiting > 0):
            response = self.arduino.readline()
            return response

    def send_command(self, command):
        # Possible commands('Start Body Position Check','Stop Body Position Check',
        #   'Start Sanitize', 'Body Release')
        commands = ['Start Body Position Check', 'Stop Body Position Check', 'Start Sanitize', 'Body Release']
        if(command in commands):
            if(command == 'Start Body Position Check'):
                self.start_body_position_check()
            elif(command == 'Stop Body Position Check'):
                self.stop_body_position_check()
            elif(command == 'Body Release'):
                self.body_release()
            elif(command == 'Start Sanitize'):
                self.start_sanitizer()
        else:
            raise Exception('Unknown command')

    def start_oximeter(self):
    #     pulse_rate_samples = []
    #     blood_saturation_samples = []
    #     count = 0
    #     while(True):
    #         red, ir = self.oximeter.read_sequential()
    #         pulse_rate, pulse_rate_valid, blood_saturation, blood_saturation_valid = hrcalc.calc_hr_and_spo2(ir[:100], red[:100])
    #         if(pulse_rate_valid and blood_saturation_valid and count <= 10):
    #             pulse_rate_samples.append(pulse_rate)
    #             blood_saturation_samples.append(blood_saturation)
    #             count = count + 1
    #         if(count > 10):
    #             break
    #     average_pulse_rate = sum(pulse_rate_samples)/len(pulse_rate_samples)
    #     average_blood_saturation = sum(blood_saturation_samples)/len(blood_saturation_samples)
        average_pulse_rate = randint(50,150)
        average_blood_saturation = randint(80,110)
        self.latest_reading['pulse_rate'] = average_pulse_rate
        self.latest_reading['blood_saturation'] = average_blood_saturation
        return average_pulse_rate, average_blood_saturation

    def start_blood_pressure_monitor(self):
        self.blood_pressure_monitor.bluetooth_communication(self.blood_pressure_monitor.patient_id_callback)
        latest_measurement = self.blood_pressure_monitor.get_measurements()[-1]
        systolic = latest_measurement[1]
        diastolic = latest_measurement[2]
        # pulse_rate = latest_measurement[3]
        self.latest_reading['systolic'] = systolic
        self.latest_reading['diastolic'] = diastolic
        # self.latest_reading['pulse_rate'] = pulse_rate
        return systolic, diastolic
            
    def save_reading(self,pulse_rate, systolic, diastolic, blood_saturation):
        blood_pressure = diastolic + ((systolic - diastolic)/3)
        date_now = datetime.now()
        values = (self.current_user.id,pulse_rate, blood_saturation, blood_pressure, systolic, diastolic, date_now, date_now)
        self.database.insert_record('readings', values)

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
    
    def speak(self, text):
        self.speaker.say(text)
        self.speaker.runAndWait()

    def set_speaker_properties(self, rate=100, volume=1.0, voice='male'):
        self.speaker.setProperty('rate', rate)
        self.speaker.setProperty('volume', volume)
        voices = self.speaker.getProperty('voices')
        if(voice == 'female'):
            self.speaker.setProperty('voice', voices[1].id)
        else:
            self.speaker.setProperty('voice', voices[0].id)

    def start_sanitizer(self):
        command = 'Start Sanitizer'
        self.arduino.write(command.encode())

    def get_current_user(self):
        try:
            if(self.current_user[0] is None):
                return None
        except:
            return self.current_user

    def get_current_pulse_rate(self):
        return self.latest_reading['pulse_rate']

    def get_current_systolic(self):
        return self.latest_reading['systolic']

    def get_current_diastolic(self):
        return self.latest_reading['diastolic']

    def get_current_blood_saturation(self):
        return self.latest_reading['blood_saturation']