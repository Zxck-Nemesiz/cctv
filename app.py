from flask import Flask, Response, render_template
import cv2
from ultralytics import YOLO

app = Flask(__name__)
model = YOLO("model/yolo11n.pt")  # Load your YOLO model

# RTSP input source
input_source = "rtsp://admin123:password123@202.184.65.40:554/stream1"

def generate_frames():
    cap = cv2.VideoCapture(input_source)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Perform YOLO object detection
        results = model(frame)

        # Annotate the frame with detection results
        annotated_frame = results[0].plot()

        # Encode the frame in JPEG format
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
