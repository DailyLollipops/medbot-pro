from database import Database
from medbot import Medbot
from tkinter import Image, messagebox
from PIL import ImageTk,Image
import tkinter
import time
from threading import Thread

class PopupMessage:
    def show_message(window, title, message, timeout = 0):
        messagebox_container = tkinter.Toplevel(window)
        messagebox_container.withdraw()
        if(timeout > 0):
            messagebox_container.after(timeout, messagebox_container.destroy)
        else:
            pass
        messagebox.showinfo(title, message, parent = messagebox_container)

class MedbotLoginGui:
    def __init__(self, medbot):
        self.window = tkinter.Tk()
        self.window.title('Login Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open('images/logo.png'))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')
        self.medbot = medbot
 
        self.placeholder = tkinter.Canvas(self.window, width = 380, height = 400)
        self.qrcode = ImageTk.PhotoImage(Image.open('images/qrcode.png').resize((128,166)))
        self.placeholder.create_text(190, 65, text = 'Med-bot: Pulse Rate\nand\nBlood Pressure Monitor',
                                anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        self.placeholder.create_image(125, 130, image = self.qrcode, anchor = tkinter.NW)
        self.placeholder.create_text(180, 355, text = 'Place your QR Code\nwithin the frame to Login',
                                anchor = tkinter.CENTER, font = ('Lucida',14), justify = 'center')
        self.placeholder.configure(background = 'white', highlightbackground = 'white' )
        self.placeholder.place(x = 0, y = 0)

        self.qrcode_scanner_frame = tkinter.Canvas(self.window, width = 400, height = 400)
        self.qrcode_scanner_frame.place(x = 390, y = 10)
        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.medbot.has_user):
            ret, frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
                self.qrcode_scanner_frame.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                try:
                    logged_in = self.medbot.login_tk(frame)
                except:
                    PopupMessage.show_message(self.window, 'Login Failed', 'Invalid Credentials', timeout = 1500)
                if(logged_in):
                    PopupMessage.show_message(self.window, 'Login Successfully', 
                                        'Welcome back, ' + self.medbot.current_user.name + ' !',
                                        timeout = 2000)
                    MedbotMainWindow(self)
        self.window.after(15, self.update)

class MedbotMainWindow():
    def __init__(self, root):
        self.root = root
        self.root.window.withdraw()
        self.window = tkinter.Toplevel(self.root.window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.title('Main Window')
        self.window.geometry('800x440')
        logo = ImageTk.PhotoImage(Image.open('images/logo.png'))
        self.window.iconphoto(False, logo)
        self.window.configure(background = 'white')

        self.body_position_check_prompted = False
        self.animation_timer = 1
        
        self.display = tkinter.Canvas(self.window, width = 700, height = 270)
        self.display_text = self.display.create_text(150, 140, text = 'Waiting to properly position arm.',
                            anchor = tkinter.W, font = ('Lucida', 20))
        self.display.place(x = 50, y = 30)

        self.pulse_rate_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.pulse_rate_icon = ImageTk.PhotoImage(Image.open('images/pulse_rate.png').resize((64,64)))
        self.pulse_rate_holder.create_image(10, 18, image = self.pulse_rate_icon, anchor = tkinter.NW)
        self.pulse_rate_holder.create_text(140, 35, text = 'Pulse Rate', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.pulse_rate_text = self.pulse_rate_holder.create_text(130, 60, text = '-- bpm',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.pulse_rate_holder.configure(background = '#f5f7fa')
        self.pulse_rate_holder.place(x = 50, y = 320)

        self.blood_pressure_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_pressure_icon = ImageTk.PhotoImage(Image.open('images/blood_pressure.png').resize((64,64)))
        self.blood_pressure_holder.create_image(10, 18, image = self.blood_pressure_icon, anchor = tkinter.NW)
        self.blood_pressure_holder.create_text(140, 35, text = 'Blood Pressure', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_pressure_text = self.blood_pressure_holder.create_text(130, 60, text = '--/-- mmHg',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_pressure_holder.configure(background = '#f5f7fa')
        self.blood_pressure_holder.place(x = 290, y = 320)

        self.blood_saturation_holder = tkinter.Canvas(self.window, width = 220, height = 100)
        self.blood_saturation_icon = ImageTk.PhotoImage(Image.open('images/blood_saturation.png').resize((64,64)))
        self.blood_saturation_holder.create_image(10, 18, image = self.blood_saturation_icon, anchor = tkinter.NW)
        self.blood_saturation_holder.create_text(140, 35, text = 'Blood Saturation', anchor = tkinter.CENTER,
                            font = ('Lucida', 15), justify = 'center')
        self.blood_saturation_text = self.blood_saturation_holder.create_text(130, 60, text = '-- %',
                            anchor = tkinter.CENTER, font = ('Lucida', 15, 'bold'), justify = 'center')
        self.blood_saturation_holder.configure(background = '#f5f7fa')
        self.blood_saturation_holder.place(x = 530, y = 320)

        self.update()

    def update(self):
        if(not self.body_position_check_prompted):
            voice_prompt = Thread(target=lambda:self.root.medbot.speak('Please position your arm properly'))
            voice_prompt.start()
            self.body_position_check_prompted = True
        self.change_display_text()
        self.window.after(15, self.update)

    def on_close(self):
        PopupMessage.show_message(self.window, 'Logout Successfully', 
                    'See you later, ' + self.root.medbot.current_user.name + ' !',
                    timeout = 3000)
        self.root.medbot.logout()
        self.root.window.deiconify()
        self.window.destroy()

    def change_display_text(self):
        if(not self.body_position_check_completed):
            if(self.animation_timer == 1):
                self.display.itemconfigure(self.display_text, text = 'Waiting to properly position arm .')
                self.animation_timer = 2
            elif(self.animation_timer == 2):
                self.display.itemconfigure(self.display_text, text = 'Waiting to properly position arm  .')
                self.animation_timer = 0
            elif(self.animation_timer == 0):
                self.display.itemconfigure(self.display_text, text = 'Waiting to properly position arm.')
                self.animation_timer = 1
            time.sleep(0.5)
                            
database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
medbot = Medbot(database)
MedbotLoginGui(medbot)
