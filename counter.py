import cv2
import numpy as np
from tracker import *
import cvzone
import mediapipe as mp
import json
from websockets.sync.client import connect

project_name = "PEOPLE COUNTER"

BaseOptions = mp.tasks.BaseOptions
ObjectDetector = mp.tasks.vision.ObjectDetector
ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

mp_drawing = mp.solutions.drawing_utils

# câmera: 0, 1...
# video: "./[nome].[formato]"
video_capture = cv2.VideoCapture("and.mp4")

cv2.namedWindow(project_name)
tracker = Tracker()

# largura e altura da tela
win_width = 1028
win_height = 500

# a distância dos dois blocos do centro
M = 250

# o ponto mais baixo e alto da tela
a2 = win_height
b1 = 0

# o ponto a esquerda e a direita que definem
# a largura da caixa
a1 = 100
b2 = 50

# a distancia entre as duas caixas
d = 400

area1 = [(a1 + M, b1), (b2 + M, b1), (b2 + M, a2), (a1 + M, a2)]
area2 = [(vertex[0] + d, vertex[1]) for vertex in area1]

er = {}
ex = {}

counter1 = []
counter2 = []

red = (0, 0, 255)
green = (0, 255, 0)

options = ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path="efficientdet_lite0.tflite"),
    max_results=5,
    running_mode=VisionRunningMode.VIDEO,
)

video_file_fps = video_capture.get(cv2.CAP_PROP_FPS)
frame_index = 0

with connect("ws://localhost:8001") as websocket:
    with ObjectDetector.create_from_options(options) as detector:
        while True:
            ret, frame = video_capture.read()

            if not ret:
                break

            frame = cv2.resize(frame, (win_width, win_height))

            list = []
            frame.flags.writeable = True
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

            frame_timestamp_ms = 1000 * frame_index / video_file_fps

            results = detector.detect_for_video(mp_image, int(frame_timestamp_ms))

            frame.flags.writeable = True
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if results.detections:
                for detection in results.detections:
                    if (
                        detection.categories[0].category_name == "person"
                        and detection.categories[0].score > 0.1
                    ):
                        bb = detection.bounding_box

                        # transformando os valores de bounding_box para inteiro
                        x, y, w, h = map(
                            int,
                            (
                                bb.origin_x,
                                bb.origin_y,
                                bb.width,
                                bb.height,
                            ),
                        )

                        cv2.rectangle(frame, (x, y), (w + x, h + y), (255, 255, 255), 3)

                        list.append([x, y, w, h])

            bbox_idx = tracker.update(list)
            for bbox in bbox_idx:
                x1, y1, x2, y2, id = bbox
                cx = int(x1 + x1 + x2) // 2
                cy = int(y1 + y1 + y2) // 2

                result = cv2.pointPolygonTest(
                    np.array(area1, np.int32), ((cx, cy)), False
                )

                if result >= 0:
                    er[id] = (cx, cy)

                if id in er:
                    result1 = cv2.pointPolygonTest(
                        np.array(area2, np.int32), ((cx, cy)), False
                    )

                    if result1 >= 0:
                        cv2.rectangle(frame, (x1, y1), (x2 + x1, y2 + y1), green, 3)
                        cvzone.putTextRect(frame, f"{id}", (cx, cy), 2, 2)
                        cv2.circle(frame, (cx, cy), 5, green, -1)

                        if counter1.count(id) == 0:
                            websocket.send(json.dumps({"payload": "ENTER"}))
                            counter1.append(id)

                result2 = cv2.pointPolygonTest(
                    np.array(area2, np.int32), ((cx, cy)), False
                )

                if result2 >= 0:
                    ex[id] = (cx, cy)

                if id in ex:
                    result3 = cv2.pointPolygonTest(
                        np.array(area1, np.int32), ((cx, cy)), False
                    )

                    if result3 >= 0:
                        cv2.rectangle(frame, (x1, y1), (x2 + x1, y2 + y1), red, 3)
                        cvzone.putTextRect(frame, f"{id}", (cx, cy), 2, 2)
                        cv2.circle(frame, (cx, cy), 5, green, -1)

                        if counter2.count(id) == 0:
                            websocket.send(json.dumps({"payload": "EXIT"}))
                            counter2.append(id)

            cv2.polylines(frame, [np.array(area1, np.int32)], True, red, 2)
            cv2.polylines(frame, [np.array(area2, np.int32)], True, red, 2)

            Enter = len(counter1)
            Exit = len(counter2)

            cvzone.putTextRect(frame, f"ENTER:-{Enter}", (50, 60), 2, 2)
            cvzone.putTextRect(frame, f"EXIT:-{Exit}", (50, 130), 2, 2)

            cv2.imshow(project_name, frame)

            frame_index += 1

            # Press 'Esc' to exit
            if cv2.waitKey(1) & 0xFF == 27:
                break


# Release the video capture and close windows
video_capture.release()
cv2.destroyAllWindows()
