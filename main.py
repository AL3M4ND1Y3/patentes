########### Dependencies ##############
import tkinter as tk
import cv2
from sys import exit as exit
import time
import requests
import os
import uuid
import tempfile
from database import subir_basededatos,obtener_username
import json
import threading

config_file = 'config.json'

if os.path.exists(config_file):
    with open(config_file, 'r') as f:   
        config = json.load(f)
else:
    # Si el archivo de configuración no existe, solicita la configuración al usuario
    config = {
        "host" : "localhost",
        "user" : "root",
        "password" : "",
        "database" : "applinkingparking",
        "port" : 3307,
        "nombre": input("Ingrese el nombre: "),
    }

    # Guarda la configuración en un archivo JSON
    with open(config_file, 'w') as f:
        json.dump(config, f)


#funcion para leer la placa
def leer_placa(img):
    try:
        regions = ['ar', 'it'] 
        with open(img, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=regions),
                files=dict(upload=fp),
                headers={'Authorization': 'Token b76c3cc286feaed0c6f30eecafaf72a183682e5d '})
            data = response.json()
        return data
    except:
        change_to_orange()


def crear_interfaz():
    global root, label, estado_pantalla

    root = tk.Tk()
    root.attributes('-fullscreen', True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    label = tk.Label(root, font=('Helvetica', 30), fg='white')
    label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    estado_pantalla = 'naranja'  # Establecer el color inicial en naranja
    change_to_orange()
    
    # Ciclo de eventos de Tkinter
    root.mainloop()

def change_to_green():
    global user_label

    root.configure(bg='green')
    label.configure(text='PASE', bg='green', fg='white')

    username = str(obtener_username(ultima_patente))
    print(username)

    # Crear una etiqueta para el nombre de usuario
    user_label = tk.Label(root, text=username, bg="green", fg="white",font=('Helvetica', 20))
    user_label.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

    root.after(2000, change_to_orange)

    global patente_detectado
    patente_detectado = False

def change_to_orange():
    global user_label

    if 'user_label' in globals():
        user_label.destroy()  # Eliminar la etiqueta del nombre de usuario

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
        change_to_green()
        global patente_detectado
        patente_detectado = False


if __name__ == "__main__":
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    patente_detectado = False
    ultima_patente = None  

    # Crear la interfaz en un hilo separado
    thread = threading.Thread(target=crear_interfaz)
    thread.start()

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
