import cv2

def get_available_cameras():
    index = 0
    available_cameras = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        cap.release()
        available_cameras.append(index)
        index += 1
    return available_cameras

print(get_available_cameras())
