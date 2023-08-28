########### Dependencies ##############
import tkinter as tk
import cv2
from sys import exit as exit
import time
import requests
import os
import uuid
import tempfile
from database import subir_basededatos

#funcion para leer la placa
def leer_placa(img):
    try:
        regions = ['ar', 'it'] 
        with open(img, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=regions),
                files=dict(upload=fp),
                headers={'Authorization': 'Token 0d85a3b4e80e65ca51f5d195739a691622c1db1a '})
            data = response.json()
        return data
    except:
        change_to_orange()


def crear_interfaz():
    global root, label

    root = tk.Tk()
    root.attributes('-fullscreen', True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    label = tk.Label(root, font=('Helvetica', 30), fg='white')
    label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

""" 
def switch_to_red():
    root.configure(bg='red')
    label.configure(text='PARE', bg='red', fg='white')
"""
def change_to_green():
    root.configure(bg='green')
    label.configure(text='PASE', bg='green', fg='white')
    root.after(2000, root.destroy)

    global patente_detectado
    patente_detectado = False

def change_to_orange():
    root.configure(bg='orange')
    label.configure(text='No se pudo leer la placa', bg='orange', fg='white')


def on_press_enter(photo_path,plate):
    data = leer_placa(photo_path)

    my_uuid = str(uuid.uuid4())
    print(my_uuid)

    foto = my_uuid + "-" + plate + ".jpg"
    ruta_guardado = r"C:\xampp\htdocs\phpPrueba\fotos"
    if not os.path.exists(ruta_guardado):
        os.makedirs(ruta_guardado)

    ruta_foto = os.path.join(ruta_guardado, foto)
    cv2.imwrite(ruta_foto, cv2.imread(photo_path))
    if subir_basededatos(foto, plate):
        crear_interfaz()
        change_to_green()
        root.mainloop()
        global patente_detectado
        patente_detectado = False


if __name__ == "__main__":
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    patente_detectado = False
    ultima_patente = None

    while True:
        ret, frame = cap.read()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            cv2.imwrite(temp_file.name, frame)

        data = leer_placa(temp_file.name)
        print(data)

        if data.get('results') and len(data['results']) > 0:
            if ultima_patente != data['results'][0]['plate']:
                patente_detectado = True
                plate = data['results'][0]['plate']
                ultima_patente = data['results'][0]['plate']
                print(ultima_patente)

                on_press_enter(temp_file.name, plate)  # Llamar a on_enter_press con la ID de cámara
            else:
                time.sleep(0.5)
                ultima_patente = None

    cap.release()
    cv2.destroyAllWindows()