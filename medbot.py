from user import User
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from base64 import b64encode,b64decode
import max30102
import hrcalc

class Medbot:
    def __init__(self, database):
        self.database = database
        self.__password = bytes('MedbotPRBPM' + '\0\0\0\0\0', 'utf-8')
        self.latest_reading = {
            'pulse_rate': None,
            'blood_pressure': None,
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
        video = cv2.VideoCapture(0)
        while True:
            ret, frame = video.read()
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
            return user
        else:
            raise Exception('Invalid Credentials')

    def start_oximeter(self):
        oximeter = max30102.MAX30102()
        pulse_rate_samples = []
        blood_saturation_samples = []
        count = 0
        while(True):
            red, ir = oximeter.read_sequential()
            pulse_rate, pulse_rate_valid, blood_saturation, blood_saturation_valid = hrcalc.calc_hr_and_spo2(ir[:100], red[:100])
            if(pulse_rate_valid and blood_saturation_valid and count <= 10):
                pulse_rate_samples.append(pulse_rate)
                blood_saturation_samples.append(blood_saturation)
                count = count + 1
            if(count > 10):
                break
        average_pulse_rate = sum(pulse_rate_samples)/len(pulse_rate_samples)
        average_blood_saturation = sum(blood_saturation_samples)/len(blood_saturation_samples)
        self.latest_reading['pulse_rate'] = average_pulse_rate
        self.latest_reading['blood_saturation'] = average_blood_saturation
        return average_pulse_rate, average_blood_saturation

    # start blood presssure monitor

    # save latest reading to database