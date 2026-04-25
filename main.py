import os
import subprocess
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, Toplevel
import cv2
import threading
import time
import deepfakeDetector
import utils
import numpy as np

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class DeepfakeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Deepfake Guardian v1.0")
        self.geometry("900x600")

        self.detector = deepfakeDetector.DeepfakeDetector()
        self.prediction_history = []
        self.guardian_active = False
        self.camera_active = False
        self.overlay_window = None

        self._setup_ui()
        self.show_upload_tab()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="DEEPFAKE\nGUARDIAN",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.tab_btn_1 = ctk.CTkButton(self.sidebar, text="Analyze File", command=self.show_upload_tab)
        self.tab_btn_1.grid(row=1, column=0, padx=20, pady=10)

        self.tab_btn_2 = ctk.CTkButton(self.sidebar, text="Live Watcher", command=self.show_live_tab)
        self.tab_btn_2.grid(row=2, column=0, padx=20, pady=10)

        self.tab_btn_3 = ctk.CTkButton(self.sidebar, text="Camera Sentry", command=self.show_camera_tab)
        self.tab_btn_3.grid(row=3, column=0, padx=20, pady=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_overlay(self):
        if self.overlay_window is None:
            try:
                self.overlay_window = Toplevel()
                self.overlay_window.overrideredirect(True)

                self.overlay_window.attributes("-topmost", True)
                self.overlay_window.attributes("-alpha", 0.9)
                self.overlay_window.geometry("320x75+0+0")

                self.overlay_window.wm_attributes("-disabled", False)

                self.overlay_label = ctk.CTkLabel(
                    self.overlay_window,
                    text="Initializing...",
                    font=("Arial", 14, "bold"),
                    fg_color="#1f1f1f",
                    text_color="white",
                    corner_radius=0
                )
                self.overlay_label.pack(expand=True, fill="both")

                self.keep_on_top()

            except Exception:
                pass

    def keep_on_top(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            if self.guardian_active or self.camera_active:
                self.overlay_window.lift()
                self.overlay_window.attributes("-topmost", True)
                self.after(200, self.keep_on_top)

    def update_overlay(self, text, color):
        try:
            if self.overlay_window and self.overlay_window.winfo_exists():
                if hasattr(self, 'overlay_label') and self.overlay_label.winfo_exists():
                    self.overlay_label.configure(text=text, text_color=color)
        except Exception:
            pass

    # def process_inference(self, img):
    #     if not self.guardian_active and not self.camera_active:
    #         return
    #
    #     face = utils.get_face_from_image(img, self.detector.mtcnn)
    #     if face:
    #         prob = self.detector.predict_face(face)
    #         self.prediction_history.append(prob)
    #         if len(self.prediction_history) > 5: self.prediction_history.pop(0)
    #         smooth = sum(self.prediction_history) / len(self.prediction_history)
    #
    #         color = "red" if smooth > 55 else ("orange" if smooth > 35 else "green")
    #         label = "FAKE" if smooth > 45 else "REAL"
    #         conf = smooth if smooth > 45 else (100 - smooth)
    #
    #         text = f"{label}: {conf:.1f}%"
    #
    #         self.after(0, lambda: self.update_overlay(text, color))
    #         self.after(0, self.safe_status_update)
    #     else:
    #         self.after(0, lambda: self.update_overlay("No Face Detected", "gray"))

    def safe_status_update(self, text, color):
        try:
            if hasattr(self, 'status_indicator') and self.status_indicator.winfo_exists():
                self.status_indicator.configure(text=f"Scanning: {text}", text_color=color)
            elif hasattr(self, 'cam_status_indicator') and self.cam_status_indicator.winfo_exists():
                self.cam_status_indicator.configure(text=f"Scanning: {text}", text_color=color)
        except Exception:
            pass

    def stop_all_active_modes(self):
        self.guardian_active = False
        self.camera_active = False
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

    def show_upload_tab(self):
        self.stop_all_active_modes()
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Choose your file (photos or videos)", font=("Arial", 16)).pack(pady=20)
        ctk.CTkButton(self.main_frame, text="Upload File", command=self.upload_file).pack(pady=10)
        self.result_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 24, "bold"))
        self.result_label.pack(pady=40)

        self.media_display_label = ctk.CTkLabel(self.main_frame, text="")
        self.media_display_label.pack(pady=10)

    def show_live_tab(self):
        self.stop_all_active_modes()
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Live-monitoring your monitor", font=("Arial", 16)).pack(pady=20)
        self.status_indicator = ctk.CTkLabel(self.main_frame, text="🔴 Inactive", text_color="red")
        self.status_indicator.pack(pady=5)
        self.toggle_btn = ctk.CTkButton(self.main_frame, text="Start Watcher", fg_color="green",
                                        command=self.toggle_guardian)
        self.toggle_btn.pack(pady=20)

    def show_camera_tab(self):
        self.stop_all_active_modes()
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Live-monitoring Webcam", font=("Arial", 16)).pack(pady=20)
        self.cam_status_indicator = ctk.CTkLabel(self.main_frame, text="📷 Camera Ready", text_color="gray")
        self.cam_status_indicator.pack(pady=5)
        self.cam_toggle_btn = ctk.CTkButton(self.main_frame, text="Start Camera", fg_color="green",
                                            command=self.toggle_camera)
        self.cam_toggle_btn.pack(pady=20)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def toggle_guardian(self):
        if self.guardian_active:
            self.stop_all_active_modes()
            self.toggle_btn.configure(text="Start Watcher", fg_color="green")
            self.status_indicator.configure(text="🔴 Inactive", text_color="red")
        else:
            self.guardian_active = True
            self.create_overlay()
            self.toggle_btn.configure(text="Stop Watcher", fg_color="red")
            self.status_indicator.configure(text="🟢 Active - Scanning Monitor...", text_color="green")
            threading.Thread(target=self.guardian_loop, daemon=True).start()

    def toggle_camera(self):
        if self.camera_active:
            self.stop_all_active_modes()
            self.cam_toggle_btn.configure(text="Start Camera", fg_color="green")
            self.cam_status_indicator.configure(text="📷 Camera Ready", text_color="gray")
        else:
            self.camera_active = True
            self.create_overlay()
            self.cam_toggle_btn.configure(text="Stop Camera", fg_color="red")
            self.cam_status_indicator.configure(text="🔵 Active - Analyzing Webcam...", text_color="blue")
            threading.Thread(target=self.camera_loop, daemon=True).start()

    def guardian_loop(self):
        while self.guardian_active:
            img = utils.capture_screen()
            self.process_inference(img)
            time.sleep(0.7)

    def camera_loop(self):
        camera_id = 0

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened() and camera_id != 0:
            cap = cv2.VideoCapture(0)

        while self.camera_active:
            ret, frame = cap.read()
            if not ret:
                self.after(0, lambda: self.cam_status_indicator.configure(
                    text="❌ Camera stream interrupted", text_color="red"))
                break

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.process_inference(img)
            time.sleep(0.5)

        cap.release()

    def process_inference(self, img):
        if not self.guardian_active and not self.camera_active:
            return

        # 1. Bild für OpenCV vorbereiten (von PIL zu numpy/cv2)
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Den schnellen Offline-Gesichtsscanner laden
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            self.after(0, lambda: self.update_overlay("Kein Gesicht erkannt", "gray"))
            self.after(0, lambda: self.safe_status_update("Kein Gesicht erkannt", "gray"))
            return

        # 2. DER TRICK: Gesichter von LINKS nach RECHTS sortieren (Anhand der X-Koordinate [f[0]])
        faces = sorted(faces, key=lambda f: (f[1] // 50, f[0]))

        probs = []
        for (x, y, w, h) in faces:
            # Gesicht ausschneiden (mit etwas Rand)
            pad_x = int(w * 0.1)
            pad_y = int(h * 0.1)
            start_x = max(0, x - pad_x)
            start_y = max(0, y - pad_y)
            end_x = min(frame.shape[1], x + w + pad_x)
            end_y = min(frame.shape[0], y + h + pad_y)

            face_roi_cv2 = frame[start_y:end_y, start_x:end_x]
            if face_roi_cv2.size == 0: continue

            # Bild ans neuronale Netz senden
            face_pil = Image.fromarray(cv2.cvtColor(face_roi_cv2, cv2.COLOR_BGR2RGB))
            face_tensor = utils.get_face_from_image(face_pil, self.detector.mtcnn)

            if face_tensor is not None:
                prob = self.detector.predict_face(face_tensor)
            else:
                prob = 50.0

            probs.append(prob)

        # 3. Text für das Overlay erstellen
        total_faces = len(probs)

        if total_faces == 1:
            # Normaler Modus bei einer Person
            p = probs[0]
            color = "red" if p > 55 else ("orange" if p > 35 else "green")
            label = "FAKE" if p > 50 else "ECHT"
            conf = p if p > 50 else (100 - p)
            text = f"{label}: {conf:.1f}%"
        else:
            # Multi-Face Modus
            fake_details = []
            for i, p in enumerate(probs):
                if p > 50:
                    # i+1, damit wir bei 1 zu zählen anfangen (Nr. 1, Nr. 2...)
                    fake_details.append(f"Nr.{i + 1} ({p:.0f}%)")

            if len(fake_details) == 0:
                self.overlay_window.geometry("320x75+0+0")
                text = f"✅ {total_faces} Gesichter: Alle Echt"
                color = "green"
            else:
                # Baut den Text zusammen: z.B. "Nr.2 (85%), Nr.3 (90%)"
                details_str = ", ".join(fake_details)
                self.overlay_window.geometry("820x75+0+0") if len(fake_details)>1 else self.overlay_window.geometry("320x75+0+0")
                text = f"⚠️ FAKE gefunden!\nPos (Lese-Richtung): {details_str}"
                color = "red"

        # 4. Updates sicher an die GUI (Haupt-Thread) senden
        self.after(0, lambda: self.update_overlay(text, color))
        # Für den Text in der Mitte ersetzen wir Zeilenumbrüche durch ein Leerzeichen
        self.after(0, lambda: self.safe_status_update(text.replace('\n', ' | '), color))

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image/Video", "*.jpg *.png *.jpeg *.mp4")])
        if not file_path: return

        self.result_label.configure(text="Analyzing in background...", text_color="white")
        self.media_display_label.configure(image="", text="")
        self.update()

        if file_path.lower().endswith(".mp4"):
            threading.Thread(target=self.analyze_video_file, args=(file_path,), daemon=True).start()
        else:
            frame = cv2.imread(file_path)
            if frame is not None:
                probs, drawn_frame = self._analyze_single_frame(frame)
                self._display_final_results(probs, drawn_frame)

    def analyze_video_file(self, file_path):
        cap = cv2.VideoCapture(file_path)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        all_probs = []
        best_frame_to_show = None

        for f in range(0, total_frames, 15):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ret, frame = cap.read()
            if not ret: break

            probs, drawn_frame = self._analyze_single_frame(frame)

            if probs:
                all_probs.extend(probs)
                best_frame_to_show = drawn_frame

        cap.release()

        self.after(0, lambda: self._display_final_results(all_probs, best_frame_to_show))

    def _analyze_single_frame(self, frame):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        probs = []
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                pad_x = int(w * 0.1)
                pad_y = int(h * 0.1)
                start_x = max(0, x - pad_x)
                start_y = max(0, y - pad_y)
                end_x = min(frame.shape[1], x + w + pad_x)
                end_y = min(frame.shape[0], y + h + pad_y)

                face_roi_cv2 = frame[start_y:end_y, start_x:end_x]
                if face_roi_cv2.size == 0: continue

                face_pil = Image.fromarray(cv2.cvtColor(face_roi_cv2, cv2.COLOR_BGR2RGB))
                face_tensor = utils.get_face_from_image(face_pil, self.detector.mtcnn)

                if face_tensor is not None:
                    prob = self.detector.predict_face(face_tensor)
                else:
                    prob = 50.0

                probs.append(prob)

                color = (0, 0, 255) if prob > 50 else (0, 255, 0)
                label_text = f"{'FAKE' if prob > 50 else 'REAL'} ({prob if prob > 50 else 100 - prob:.1f}%)"

                cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), color, 3)
                cv2.rectangle(frame, (start_x, start_y - 30), (end_x, start_y), color, cv2.FILLED)
                cv2.putText(frame, label_text, (start_x + 5, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 255, 255), 2)

        return probs, frame

    def _display_final_results(self, all_probs, drawn_frame):
        if not all_probs:
            self.result_label.configure(text="No face found in file!", text_color="orange")
            self.media_display_label.configure(image="", text="No faces to display")
            return

        avg = sum(all_probs) / len(all_probs)
        if avg > 50:
            self.result_label.configure(text=f"AVERAGE RESULT: FAKE ({avg:.1f}%)", text_color="red")
        else:
            self.result_label.configure(text=f"AVERAGE RESULT: REAL ({100 - avg:.1f}%)", text_color="green")

        if drawn_frame is not None:
            if drawn_frame.shape[1] > 500:
                scale_percent = 500 / drawn_frame.shape[1]
                new_width = int(drawn_frame.shape[1] * scale_percent)
                new_height = int(drawn_frame.shape[0] * scale_percent)
                drawn_frame = cv2.resize(drawn_frame, (new_width, new_height))

            final_img_pil = Image.fromarray(cv2.cvtColor(drawn_frame, cv2.COLOR_BGR2RGB))
            ctk_image = ctk.CTkImage(light_image=final_img_pil, size=(drawn_frame.shape[1], drawn_frame.shape[0]))

            self.media_display_label.configure(image=ctk_image, text="")
            self.media_display_label.image = ctk_image

if __name__ == "__main__":
    app = DeepfakeApp()
    app.mainloop()