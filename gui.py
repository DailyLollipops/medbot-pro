from database import Database
from medbot import Medbot
from tkinter import Image, messagebox
from PIL import ImageTk,Image
import tkinter

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
    def __init__(self, window_title, medbot):
        self.window = tkinter.Tk()
        self.window.title(window_title)
        self.window.geometry('600x400')
        self.medbot = medbot

        title_label = tkinter.Label(self.window, text = 'Med-bot: Pulse Rate\nand\nBlood Pressure Monitor',
                                        anchor = tkinter.CENTER, font = ('Lucida',15))
        title_label.place(x = 30, y = 50)

        logo = ImageTk.PhotoImage(Image.open('logo.png')) 
        logo_holder = tkinter.Canvas(self.window, width = 128, height = 128)
        logo_holder.place(x = 30, y = 100)
        logo_holder.create_image(0, 0, image = logo , anchor = tkinter.CENTER)

        self.canvas = tkinter.Canvas(self.window, width = 300, height = 350)
        self.canvas.place(x=275, y=25)
        self.update()
        self.window.mainloop()

    def update(self):
        if(not self.medbot.has_user):
            ret, frame = self.medbot.get_qrcode_scanner_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
                logged_in = self.medbot.login_tk(frame)
                if(logged_in):
                    PopupMessage.show_message(self.window, 'Login Successfully', 
                                        'Welcome Back ' + self.medbot.current_user.name + ' !',
                                        timeout = 2000)
                    MedbotMainWindow(self)
        self.window.after(15, self.update)

class MedbotMainWindow():
    def __init__(self, root):
        self.root = root
        self.root.window.withdraw()
        self.window = tkinter.Toplevel(self.root.window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update()

    def update(self):
        self.window.after(15, self.update)

    def on_close(self):
        PopupMessage.show_message(self.window, 'Logout Successfully', 
                    'See you later ' + self.root.medbot.current_user.name + ' !',
                    timeout = 3000)
        self.root.medbot.logout()
        self.root.window.deiconify()
        self.window.destroy()

database = Database('sql.freedb.tech','freedb_medbot','freedb_medbot','ct9xVSS$$2g35s7')
medbot = Medbot(database)
MedbotLoginGui("Tkinter and OpenCV",medbot)
