import numpy as np
import threading, time, traceback, cv2, os, ctypes, platform, queue, threading
import sys
from ctypes import POINTER, c_int, c_uint, c_double
from PIL import Image, ImageDraw, ImageFont


class Camera(object):

    def __init__(self, type="", index=0, name="", config=None):

        self.types = {
            "Height":int,
            "Width":int,
            "OffsetX":int,
            "OffsetY":int,
            "index":int,
            "name":str,
            "dtype":str,
            "type":[
                "webcam",
                "spinnaker",
                "andor",
                "test"
            ],
            "master":bool
        }

        for k, v in config.items():
            self._set(k,v)

        if not self.type and type not in self.types["type"]:
            raise Exception("You must indicate a Camera Type.")

        self._start()

        threading.Thread(target=self._update_frame).start()

    def _start(self):

        self.frame = np.zeros((500,500), dtype="uint8")

        if self.type == "webcam":
            self._camera = cv2.VideoCapture(self.index)
            ret, frame = self._camera.read()
            if not ret:
                self.error_msg = "No webcam found at index: {0}".format(self.index)
            else:
                self.error_msg = ""

        elif self.type == "spinnaker":
            try:
                import PySpin
            except Exception as e:
                msg= str(e)+"\n\nFollow the directions here:\
                \n\n\thttps://github.com/ryan-byrne/pywfom/wiki/Cameras:-Spinnaker\n"
                print(msg)
                self.error_msg = msg

        elif self.type == "andor":
            try:
                from pywfom import andor
            except Exception as e:
                msg = str(e)+"\n\nFollow the directions here:\
                    \n\n\thttps://github.com/ryan-byrne/pywfom/wiki/Cameras:-Installing-the-Andor-SDK3\n"
                print(msg)
                self.error_msg = msg

        else:
            self.error_msg = ""

        self.active = True

    def _stop(self):

        if self.type == "webcam":
            pass

    def _update_frame(self):
        while self.active:

            # Ignore is error
            if self.error_msg != "":
                self._error_frame()
                continue

            # Generates a numpy array for the self.frame variable
            if self.type == "webcam":
                self.frame = self._get_webcam_frame()

            elif self.type == "spinnaker":
                self.frame = self._get_spinnaker_frame()

            elif self.type == "andor":
                self.frame = self._get_andor_frame()

            else:
                self.frame = self._get_test_frame()

    def _error_frame(self):

        img = Image.fromarray(np.zeros((500,500), "uint8"))
        draw = ImageDraw.Draw(img)
        draw.text((10, 175), "ERROR:", 255)
        draw.text((10,225), self.error_msg, 255)
        self.frame = np.asarray(img)

    def _get_andor_frame(self):
        # If not paused or testing, get next buffer from camera
        try:
            buf = self._buffers.get()
            WaitBuffer(self._handle, 100)
            self.error_msg = ""
            # Reformat buffer to a frame
            frame = np.array(buf).view(np.uint16).reshape((self.height, self.width))
            # Queue up next buffer
            QueueBuffer(self._handle, buf.ctypes.data_as(POINTER(AT_U8)), buf.nbytes)
            self._buffers.put(buf)
            return frame
        except:
            self.error_msg = "Unable to read {1} ( {0}:{2} )".format(self.type,self.name,self.index)

    def _get_webcam_frame(self):
        try:
            frame = self._camera.read()[1]
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.error_msg = ""
            x, y, w, h = self.OffsetX, self.OffsetY, self.Width, self.Height
            return frame[y:h+y, x:w+x]
        except Exception as e:
            self.error_msg = str(e)

    def _get_spinnaker_frame(self):
        try:
            image_result = self._camera.GetNextImage(1000)
            img = np.reshape(   image_result.GetData(),
                                (image_result.GetHeight(),image_result.GetWidth())
                            )
            image_result.Release()
            self.frame = img
            self.error_msg = ""
        except:
            self.error_msg = "Unable to read {1} ( {0}:{2} )".format(self.type,self.name,self.index)

    def _get_test_frame(self):

        if self.dtype == 'uint8':
            max = 255
        else:
            max = 65024

        return np.random.randint(0,max,size=(self.Height, self.Width), dtype=self.dtype)

    def set(self, param, value=None):

        # TODO: Change camera type -> check if andor

        self._stop()

        if type(param).__name__ == 'dict':
            for k, v in param.items():
                self._set(k, v)
        else:
            self._set(param, value)

        self._start()

    def _set(self, param, value):

        if param in ["camera"]:
            return

        setattr(self, param, value)

    def get(self, param):
        pass

    def _get(self, param):
        pass

    def get_max(self, param):
        if self.type in ["webcam", "test"]:
            if param == "Height":
                return 700
            elif param == "Width":
                return 1200

    def close(self):
        self.active = False
