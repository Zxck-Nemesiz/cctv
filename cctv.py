from flask import Flask, Response, render_template, request, send_file
import cv2
import pytesseract
import tempfile
import os
import mammoth
from pdf2image import convert_from_path
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
        #print(results[0].names)
        
        for result in results:
            detection_count = result.boxes.shape[0]

            for i in range(detection_count):
                cls = int(result.boxes.cls[i].item())
                name = result.names[cls]
                print(name)

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

@app.route('/cctv')
def cctv():
    return render_template('cctv.html')

@app.route('/pdf')
def pdf():
    return render_template('pdf.html')

@app.route('/pdf', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('pdf.html', text_data="No file uploaded")
        file = request.files['file']
        if file.filename == '':
            return render_template('pdf.html', text_data="No file selected")
        if file:
            if file.filename[-1] != 'f' and file.filename[-1] != 'x' and file.filename[-1] != 'c':
                return render_template('pdf.html', text_data="File format not supported")
            
            text_data = ''
            if file.filename[-1] == 'f':
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                # convert to image using resolution 600 dpi 
                pages = convert_from_path(temp_file_path, 600)

                # extract text
                for page in pages:
                    text = pytesseract.image_to_string(page)
                    text_data += text + '\n'
            
            else:
                if file.filename[-1] == 'x':
                    suffix = '.docx'
                else:
                    suffix = '.doc'
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                    
                def read_docx_with_mammoth(docx_path):
                    with open(docx_path, "rb") as docx_file:
                        result = mammoth.extract_raw_text(docx_file)
                    return result.value

                text_data = read_docx_with_mammoth(temp_file_path)
                
            print(text_data)
            
            os.remove(temp_file_path)
    return render_template('pdf.html', text_data=text_data)
 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
