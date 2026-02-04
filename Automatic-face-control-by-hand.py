# Importing Necessary Packages 
import cv2
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp

class FaceGestureApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Smart Face Detection with Hand Gesture Control")

        # Make window fill most of the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.9)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="#e9ecf3")

        # MediaPipe Setup
        self.mp_hands = mp.solutions.hands
        self.mp_face = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils

        # ➕ ADDED: Face Mesh setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5
        )
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )

        self.face_detection_enabled = False
        self.video_running = False
        self.cap = cv2.VideoCapture(0)

        self.create_ui()

    # UI Layout
    def create_ui(self):
        """Setup Tkinter UI layout."""

        # Create main layout frames using grid (for stable scaling)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # HEADER
        title_frame = tk.Frame(self.root, bg="#6c63ff", height=80)
        title_frame.grid(row=0, column=0, sticky="nsew")
        title_frame.grid_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 Smart Face Detection Controlled by Hand Gestures",
            font=("Helvetica", 22, "bold"),
            bg="#6c63ff",
            fg="white",
        )
        title_label.pack(expand=True)

        # VIDEO SECTION
        video_frame = tk.Frame(self.root, bg="#e9ecf3")
        video_frame.grid(row=1, column=0, sticky="nsew")
        video_frame.grid_rowconfigure(0, weight=1)
        video_frame.grid_columnconfigure(0, weight=1)

        video_border = tk.Frame(video_frame, bg="#bdbdbd", bd=4, relief="ridge")
        video_border.pack(pady=20, expand=True)

        self.video_label = tk.Label(video_border, bg="black")
        self.video_label.pack(expand=True)

        # STATUS
        self.status_label = tk.Label(
            self.root,
            text="🖐 Use Pinky finger to enable face detection, Index finger to disable it",
            font=("Helvetica", 15, "bold"),
            fg="#4b0082",
            bg="#e9ecf3",
            wraplength=1000,
            justify="center",
        )
        self.status_label.grid(row=2, column=0, pady=20, sticky="nsew")

        # BUTTONS
        btn_frame = tk.Frame(self.root, bg="#e9ecf3")
        btn_frame.grid(row=3, column=0, pady=20)
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        button_style = {
            "font": ("Helvetica", 14, "bold"),
            "fg": "white",
            "relief": "flat",
            "padx": 15,
            "pady": 10,
            "width": 18,
            "cursor": "hand2",
        }

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Detection",
            command=self.start_video,
            bg="#6c63ff",
            activebackground="#5a52e0",
            **button_style,
        )
        self.start_btn.grid(row=0, column=0, padx=20, sticky="ew")

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏸ Stop Detection",
            command=self.stop_video,
            bg="#ff9800",
            activebackground="#e68900",
            **button_style,
        )
        self.stop_btn.grid(row=0, column=1, padx=20, sticky="ew")

        self.exit_btn = tk.Button(
            btn_frame,
            text="❌ Exit Application",
            command=self.exit_app,
            bg="#f44336",
            activebackground="#d32f2f",
            **button_style,
        )
        self.exit_btn.grid(row=0, column=2, padx=20, sticky="ew")

    # Hand Logic 
    def count_extended_fingers(self, hand_landmarks):
        """Count which fingers are extended."""
        finger_states = []
        landmarks = hand_landmarks.landmark

        # Thumb (compare x-coordinates)
        finger_states.append(landmarks[4].x < landmarks[3].x)
        # Other fingers
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for tip, pip in zip(tips, pips):
            finger_states.append(landmarks[tip].y < landmarks[pip].y)
        return finger_states

    # Frame Update
    def update_frame(self):
        """Capture and process each frame."""
        if not self.video_running:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_height, image_width = frame.shape[:2]
        status_text = ""

        # Hand detection
        results_hands = self.hands.process(frame_rgb)
        if results_hands.multi_hand_landmarks:
            for hand_landmarks in results_hands.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(255, 0, 127), thickness=2, circle_radius=4),
                    self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2),
                )

                fingers = self.count_extended_fingers(hand_landmarks)
                if fingers[4]:  # Pinky
                    self.face_detection_enabled = True
                    status_text = "🌸 Pinky Finger Detected → Face Detection ON"
                elif fingers[1]:  # Index
                    self.face_detection_enabled = False
                    status_text = "☝️ Index Finger Detected → Face Detection OFF"

        # Face detection
        if self.face_detection_enabled:
            results_face = self.face_detection.process(frame_rgb)
            if results_face.detections:
                for detection in results_face.detections:
                    bboxC = detection.location_data.relative_bounding_box

                    confidence = detection.score[0]

                    if confidence > 0.9:

                        x, y, w, h = (
                            int(bboxC.xmin * image_width),
                            int(bboxC.ymin * image_height),
                            int(bboxC.width * image_width),
                            int(bboxC.height * image_height),
                        )

                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,0,255), 3)
                        cv2.putText(
                            frame,
                            f"Face & Conf: {confidence * 100:.2f}%",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (255,0,0),
                            2,
                        )

            # ➕ ADDED: Face Mesh Processing
            results_mesh = self.face_mesh.process(frame_rgb)
            if results_mesh.multi_face_landmarks:
                for face_landmarks in results_mesh.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        face_landmarks,
                        self.mp_face_mesh.FACEMESH_TESSELATION,
                        self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                        self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1),
                    )

        # Update status
        if status_text:
            self.status_label.config(text=status_text)

        # Display frame in Tkinter
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self.root.after(10, self.update_frame)

    # Control Buttons
    def start_video(self):
        if not self.video_running:
            self.video_running = True
            self.status_label.config(text="🎥 Starting video...")
            self.update_frame()

    def stop_video(self):
        self.video_running = False
        self.status_label.config(text="⏸ Video stopped.")

    def exit_app(self):
        self.video_running = False
        self.cap.release()
        self.root.destroy()


# Run App 
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceGestureApp(root)
    root.mainloop()
    cv2.destroyAllWindows()
