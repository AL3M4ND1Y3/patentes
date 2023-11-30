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
import threading
from contorno import detectar_contorno_patente
import configparser

#funcion para leer la placa
def leer_placa(img):
    try:
        regions = ['ar', 'it'] 
        with open(img, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=regions),
                files=dict(upload=fp),
                headers={'Authorization': f'Token {os.environ.get("API_KEY", "")} '})
            data = response.json()
        return data
    except:
        change_to_orange()


def crear_interfaz():
    global root, label, estado_pantalla

    root = tk.Tk()
    root.attributes('-fullscreen', True)


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

    root.after(6000, change_to_orange)


def change_to_orange():
    global user_label

    if 'user_label' in globals():
        user_label.destroy()  # Eliminar la etiqueta del nombre de usuario

    root.configure(bg='orange')
    label.configure(text='Bienvenido.Coloquese ante la camara', bg='orange', fg='white')

"""     global patente_detectado
    patente_detectado = False """

def on_press_enter(photo_path,plate):

    leer_placa(photo_path)

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

if __name__ == "__main__":
    config = configparser.ConfigParser()
    
    config.read('config.ini')

    numero_camara = config.getint('Configuracion', 'NumeroCamara', fallback=0)
    cap = cv2.VideoCapture(numero_camara, cv2.CAP_DSHOW)
    patente_detectado = False
    ultima_patente = None 
    estado_pantalla = None

    # Crear la interfaz en un hilo separado
    thread = threading.Thread(target=crear_interfaz)
    thread.start()

    while True:
        if estado_pantalla == 'naranja' and not patente_detectado:
            ret, frame = cap.read()
            patente_detectado, frame = detectar_contorno_patente(frame)


        if patente_detectado:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                cv2.imwrite(temp_file.name, frame)
            
            data = leer_placa(temp_file.name)
            print(data)

            if data.get('results') and len(data['results']) > 0:
                if ultima_patente != data['results'][0]['plate']:
                    patente_detectado = False  # Establecer a False para que pueda detectar nuevas placas
                    plate = data['results'][0]['plate']
                    ultima_patente = data['results'][0]['plate']
                    print(ultima_patente)
                    on_press_enter(temp_file.name, plate)  # Llamar a on_enter_press con la ID de cámara
                else:
                    time.sleep(0.5)
                    ultima_patente = None