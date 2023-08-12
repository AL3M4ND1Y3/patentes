########### Dependencies ##############
import tkinter as tk
import cv2
from sys import exit as exit
from datetime import datetime
import time
import requests
import mysql.connector as db
import json
from datetime import datetime
import os
import uuid
import tempfile
import re

#funcion para leer la placa
def leer_placa(img):
    try:
        regions = ['ar', 'it'] # estos parametros depende del tipo de placa a leer segun el pais
        # Se abre el archivo de datos .csv
        with open(img, 'rb') as fp:
            #se pide la consulta al servidor
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=regions),  # Opcional
                # se sube la foto al servidor
                # Se le envia el token a la APi de la web http://docs.platerecognizer.com/
                # Aqui tienes que colocar tu propio Token suscribiendote a la pagina
                files=dict(upload=fp),
                headers={'Authorization': 'Token 0b502181ff4025f2c1be56443a838c6b80fbebb9 '})
            data = response.json
        return response.json()#retorna el json con los datos procesados
    except:
        change_to_orange()

def subir_basededatos(data, foto_patente, license_plate):
    with open('database.json') as database_file:
        keys = json.load(database_file)

    # Crear conexión a la base de datos
    conex = db.connect(
        host=keys["host"],
        user=keys["user"],
        password=keys["password"],
        database=keys["database"],
        port=keys["port"]
    )
    cursor = conex.cursor()

    if data['results']:
        # Verificar si la placa ya está registrada en la tabla "vehiculos"
        query = "SELECT * FROM vehiculos WHERE placa = %s"
        cursor.execute(query, (license_plate,))
        result = cursor.fetchone()

        if result:
            # La placa existe en la tabla "vehiculos"
            vehiculo_id = result[0]  # Obtener el ID del vehículo

            # Verificar si el vehículo ya tiene una entrada y salida registradas
            query = "SELECT fecha_entrada, fecha_salida FROM registros_entradas_salidas WHERE vehiculo_id = %s ORDER BY fecha_entrada DESC LIMIT 1"
            cursor.execute(query, (vehiculo_id,))
            result = cursor.fetchone()

            if result:
                hora_entrada, hora_salida = result
                if hora_entrada and hora_salida:
                    # Si el vehículo ya tiene entrada y salida, se agrega una nueva fila con una nueva entrada
                    fecha_hora = datetime.now()
                    query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, 1, 1, %s, %s, 1000)"
                    cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
                    conex.commit()
                elif hora_entrada and not hora_salida:
                    # Si el vehículo ya tiene entrada y no tiene salida, se agrega como salida con la foto correspondiente
                    fecha_hora = datetime.now()
                    query = "UPDATE registros_entradas_salidas SET fecha_salida = %s WHERE vehiculo_id = %s AND fecha_entrada = %s"
                    cursor.execute(query, (fecha_hora, vehiculo_id, hora_entrada))
                    conex.commit()
                else:
                    # Si el vehículo no tiene entrada o ya tiene entrada y salida, se agrega como entrada
                    fecha_hora = datetime.now()
                    query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, 1, 1, %s, %s, 1000)"
                    cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
                    conex.commit()
            else:
                # El vehículo no tiene entradas ni salidas registradas, se agrega como entrada
                fecha_hora = datetime.now()
                query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, 1, 1, %s, %s, 1000)"
                cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
                conex.commit()
        else:
            # La placa no existe en la tabla "vehiculos"
            fecha_hora = datetime.now()
            query = "INSERT INTO vehiculos (placa, tipo_vehiculo_id,color_id,marca_id,modelo_id) VALUES (%s,1,1,2,1)"
            cursor.execute(query, (license_plate,))
            vehiculo_id = cursor.lastrowid  # Obtener el ID del vehículo recién insertado
            conex.commit()

            # Insertar en la tabla "registros_entradas_salidas" con el ID del vehículo recién insertado
            query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, 1, 1, %s, %s, 1000)"
            cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
            conex.commit()

    # Cerrar conexión a la base de datos
    try:
        cursor.close()
    except:
        pass
    finally:
        conex.close()
    return True

def crear_interfaz():
    global root, label

    root = tk.Tk()
    root.attributes('-fullscreen', True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    label = tk.Label(root, font=('Helvetica', 30), fg='white')
    label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


def switch_to_red():
    root.configure(bg='red')
    label.configure(text='PARE', bg='red', fg='white')

def change_to_green():
    root.configure(bg='green')
    label.configure(text='PASE', bg='green', fg='white')
    root.after(2000, root.destroy)

    global patente_detectado
    patente_detectado = False

def change_to_orange():
    root.configure(bg='orange')
    label.configure(text='No se pudo leer la placa', bg='orange', fg='white')


def on_enter_press(photo_path):
    data = leer_placa(photo_path)
    print(data)

    if data.get('results') and len(data['results']) > 0:
        plate = data['results'][0]['plate']

        my_uuid = str(uuid.uuid4())
        print(my_uuid)

        foto = my_uuid + "-" + plate + ".jpg"
        ruta_guardado = r"C:\xampp\htdocs\phpPrueba\fotos"
        #Si no existe la ruta para guardar la foto, lo crea
        if not os.path.exists(ruta_guardado):
            os.makedirs(ruta_guardado)

        ruta_foto = os.path.join(ruta_guardado, foto)
        cv2.imwrite(ruta_foto, cv2.imread(photo_path))
        if subir_basededatos(data, foto, plate):
            crear_interfaz()
            change_to_green()  # Cambiar a verde y cerrar después de subir a la base de datos
            root.mainloop()
        else:
            change_to_orange()

if __name__ == "__main__":
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    patente_detectado = False
    ultima_patente = None

    while not patente_detectado:
        ret, frame = cap.read()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            cv2.imwrite(temp_file.name, frame)

        data = leer_placa(temp_file.name)
        print(data)

        if data.get('results') and len(data['results']) > 0:
            if ultima_patente != data['results'][0]['plate']:
                patente_detectado = True
                ultima_patente = data['results'][0]['plate']
                print(ultima_patente)

                on_enter_press(temp_file.name)  # Llamar directamente a la función
            else:
                time.sleep(0.5)
                ultima_patente = None
                                
    cap.release()
    cv2.destroyAllWindows()




