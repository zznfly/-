import tkinter as tk
from tkinter.filedialog import *
from tkinter import ttk
import predict
import cv2
from PIL import Image, ImageTk
import threading
import time
import requests
import base64
import easygui as g


class Surface(ttk.Frame):
    pic_path = ""
    viewhigh = 600
    viewwide = 600
    update_time = 0
    thread = None
    thread_run = False
    color_transform = {"green": ("绿牌", "#55FF55"), "yello": ("黄牌", "#FFFF00"), "blue": ("蓝牌", "#6666FF")}

    def __init__(self, win):
        ttk.Frame.__init__(self, win)
        frame_left = ttk.Frame(self)
        frame_right1 = ttk.Frame(self)
        frame_right2 = ttk.Frame(self)
        win.title("车牌号识别")
        win.state("zoomed")
        self.pack(fill=tk.BOTH, expand=tk.YES, padx="5", pady="5")
        frame_left.pack(side=LEFT, expand=1, fill=BOTH)
        frame_right1.pack(side=TOP, expand=1, fill=tk.Y)
        frame_right2.pack(side=RIGHT, expand=0)
        ttk.Label(frame_left, text='原图：').pack(anchor="nw")
        ttk.Label(frame_right1, text='车牌位置：').grid(column=0, row=0, sticky=tk.W)

        from_pic_ctl = ttk.Button(frame_right2, text="本地识别", width=20, command=self.from_pic)
        from_net_ctl = ttk.Button(frame_right2, text="网络识别", width=20, command=self.from_net)
        self.image_ctl = ttk.Label(frame_left)
        self.image_ctl.pack(anchor="nw")

        self.roi_ctl = ttk.Label(frame_right1)
        self.roi_ctl.grid(column=0, row=1, sticky=tk.W)
        ttk.Label(frame_right1, text='识别结果：').grid(column=0, row=2, sticky=tk.W)
        self.r_ctl = ttk.Label(frame_right1, text="")
        self.r_ctl.grid(column=0, row=3, sticky=tk.W)
        self.color_ctl = ttk.Label(frame_right1, text="", width="20")
        self.color_ctl.grid(column=0, row=4, sticky=tk.W)
        from_net_ctl.pack(anchor="se", pady="5")
        from_pic_ctl.pack(anchor="se", pady="5")
        self.predictor = predict.CardPredictor()
        self.predictor.train_svm()

    def get_imgtk(self, img_bgr):
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im)
        wide = imgtk.width()
        high = imgtk.height()
        if wide > self.viewwide or high > self.viewhigh:
            wide_factor = self.viewwide / wide
            high_factor = self.viewhigh / high
            factor = min(wide_factor, high_factor)
            wide = int(wide * factor)
            if wide <= 0: wide = 1
            high = int(high * factor)
            if high <= 0: high = 1
            im = im.resize((wide, high), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=im)
        return imgtk

    def show_roi(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi = ImageTk.PhotoImage(image=roi)
            self.roi_ctl.configure(image=self.imgtk_roi, state='enable')
            self.r_ctl.configure(text=str(r))
            self.update_time = time.time()
            try:
                c = self.color_transform[color]
                self.color_ctl.configure(text=c[0], background=c[1], state='enable')
            except:
                self.color_ctl.configure(state='disabled')
        elif self.update_time + 8 < time.time():
            self.roi_ctl.configure(state='disabled')
            self.r_ctl.configure(text="")
            self.color_ctl.configure(state='disabled')

    def from_net(self):
        if self.thread_run:
            return
        global imgurl
        imgurl = g.fileopenbox('选择文件', '提示', 'C:/Users/admin/Desktop/')

        if imgurl:

            host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=AxzSTIGeXDSDDP2Wu5elaHnv&client_secret=gWKIBjBzSRDQOl4pyd6G33khnOamg1pV'
            headers = {
                'Content-Type': 'application/json;charset=UTF-8'
            }
            res = requests.get(url=host, headers=headers).json()
            print(res['access_token'])
            url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/license_plate'
            data = {}
            data['access_token'] = res['access_token']
            image = get_file_content(imgurl)
            data['image'] = base64.b64encode(image)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "apikey": "AxzSTIGeXDSDDP2Wu5elaHnv"
            }
            res = requests.post(url=url, headers=headers, data=data)
            result = res.json()

            # print(result["words_result"]['color'])
            # print(result["words_result"]['number'])
            color = result["words_result"]['color']
            number = result["words_result"]['number']
            roi = self.get_value()

            self.show_roi(number, roi, color)
            return
        self.thread = threading.Thread(target=self.net_thread, args=(self,))
        self.thread.setDaemon(True)
        self.thread.start()
        self.thread_run = True

    def from_pic(self):
      try:
        self.thread_run = False
        self.pic_path = askopenfilename(title="选择识别图片", filetypes=[("jpg图片", "*.jpg")])
        print(self.pic_path)
        if self.pic_path:
            img_bgr = predict.imreadex(self.pic_path)
            self.imgtk = self.get_imgtk(img_bgr)
            self.image_ctl.configure(image=self.imgtk)
            r, roi, color = self.predictor.predict(img_bgr)
            # print(roi)
            self.show_roi(r, roi, color)
      except():
          tk.messagebox.showwarning('错误', '图片无法识别！')

    def get_value(self):
        global imgurl
        print(imgurl)
        self.thread_run = False
        self.pic_path = imgurl
        print(self.pic_path)
        if self.pic_path:
            img_bgr = predict.imreadex(self.pic_path)
            self.imgtk = self.get_imgtk(img_bgr)
            self.image_ctl.configure(image=self.imgtk)
            r, roi, color = self.predictor.predict(img_bgr)
            # print(roi)
        return  roi



# def net_thread(self):
# 	self.thread_run = True
# 	predict_time = time.time()
# 	while self.thread_run:
# 		_, img_bgr = self.camera.read()
# 		self.imgtk = self.get_imgtk(img_bgr)
# 		self.image_ctl.configure(image=self.imgtk)
# 		if time.time() - predict_time > 2:
# 			r, roi, color = self.predictor.predict(img_bgr)
# 			self.show_roi(r, roi, color)
# 			predict_time = time.time()
# 	print("run end")


def get_file_content(filePath):
    with open(filePath, "rb") as fp:
        return fp.read()

def close_window():
    print("destroy")
    if surface.thread_run:
        surface.thread_run = False
        surface.thread.join(2.0)
    win.destroy()


if __name__ == '__main__':
    win = tk.Tk()
try:
    surface = Surface(win)
    win.protocol('WM_DELETE_WINDOW', close_window)
    win.mainloop()
except():
    tk.messagebox.showwarning('错误', '图片无法识别！')
