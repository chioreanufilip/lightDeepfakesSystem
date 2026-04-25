import cv2
from PIL import Image
from mss import mss

def get_face_from_image(img, mtcnn_model):
    boxes, _ = mtcnn_model.detect(img)
    if boxes is not None:
        box = boxes[0].astype(int)
        face_img = img.crop((max(0, box[0]), max(0, box[1]), box[2], box[3]))
        return face_img
    return None

def capture_screen():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

