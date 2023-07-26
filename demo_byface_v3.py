########### Dependencies ##############
import tkinter as tk
import cv2
from sys import exit as exit
from datetime import datetime
import requests
import mysql.connector as db
import json
from datetime import datetime
import os
import uuid
import tempfile
import re

# Parametros
max_num_plate=10 # maximo numero de placas a almacenar en el fichero .csv

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
                headers={'Authorization': 'Token 6d24aef7d7c96f849022ac2adf6c8afa6768f5ee '})
            data = response.json
        return response.json()#retorna el json con los datos procesados
    except:
        switch_to_orange()



# funcion para validar y guardar la placa leida
def subir_basededatos(data, max_num_plates, foto_patente):
    with open('database.json') as database_file:
        keys = json.load(database_file)
    
    # Crear conexión a la base de datos
    conex = db.connect(
        host=keys["host"],
        user=keys["user"],
        password=keys["password"],
        database=keys["database"],
        port = keys["port"]
    )
    cursor = conex.cursor()

    if data['results']:
        # Obtener la placa de la imagen y convertirla a mayúsculas
        license_plate = data['results'][0]['plate'].upper()
        print(license_plate)

        # Verificar si la placa ya está registrada en la tabla "vehiculos"
        query = "SELECT * FROM vehiculos WHERE placa = %s"
        cursor.execute(query, (license_plate,))
        result = cursor.fetchone()

        if result:
            # La placa existe en la tabla "vehiculos"
            vehiculo_id = result[0]  # Obtener el ID del vehículo

            # Verificar si el vehículo ya tiene una entrada y salida registradas
            query = "SELECT hora_entrada, hora_salida FROM registros_entrada_salida WHERE vehiculo_id = %s ORDER BY hora_entrada DESC LIMIT 1"
            cursor.execute(query, (vehiculo_id,))
            result = cursor.fetchone()

            if result:
                hora_entrada, hora_salida = result
                if hora_entrada and hora_salida:
                    # Si el vehículo ya tiene entrada y salida, se agrega una nueva fila con una nueva entrada
                    fecha_hora = datetime.now()
                    query = "INSERT INTO registros_entrada_salida (vehiculo_id, espacio_estacionamiento_id, hora_entrada, tarifa, foto_vehiculo) VALUES (%s, 1, %s, 1000, %s)"
                    cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
                    conex.commit()
                elif hora_entrada and not hora_salida:
                    # Si el vehículo ya tiene entrada y no tiene salida, se agrega como salida con la foto correspondiente
                    fecha_hora = datetime.now()
                    query = "UPDATE registros_entrada_salida SET hora_salida = %s WHERE vehiculo_id = %s AND hora_entrada = %s"
                    cursor.execute(query, (fecha_hora, vehiculo_id, hora_entrada))
                    conex.commit()
                else:
                    # Si el vehículo no tiene entrada o ya tiene entrada y salida, se agrega como entrada
                    fecha_hora = datetime.now()
                    query = "INSERT INTO registros_entrada_salida (vehiculo_id, espacio_estacionamiento_id, hora_entrada, tarifa, foto_vehiculo) VALUES (%s, 1, %s, 1000, %s)"
                    cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
                    conex.commit()
            else:
                # El vehículo no tiene entradas ni salidas registradas, se agrega como entrada
                fecha_hora = datetime.now()
                query = "INSERT INTO registros_entrada_salida (vehiculo_id, espacio_estacionamiento_id, hora_entrada, tarifa, foto_vehiculo) VALUES (%s, 1, %s, 1000, %s)"
                cursor.execute(query, (vehiculo_id, fecha_hora,foto_patente))
                conex.commit()
        else:
            # La placa no existe en la tabla "vehiculos"
            fecha_hora = datetime.now()
            query = "INSERT INTO vehiculos (placa, modelo_id, color_id) VALUES (%s, NULL, NULL)"
            cursor.execute(query, (license_plate,))
            vehiculo_id = cursor.lastrowid  # Obtener el ID del vehículo recién insertado
            conex.commit()

            # Insertar en la tabla "registros_entrada_salida" con el ID del vehículo recién insertado
            query = "INSERT INTO registros_entrada_salida (vehiculo_id, espacio_estacionamiento_id, hora_entrada, tarifa, foto_vehiculo) VALUES (%s, 1, %s, 1000, %s)"
            cursor.execute(query, (vehiculo_id, fecha_hora, foto_patente))
            conex.commit()


    # Cerrar conexión a la base de datos
    try:
        cursor.close()
    except:
        pass
    finally:
        conex.close()



def switch_to_red():
    root.configure(bg='red')
    label.configure(text='PARE', bg='red', fg='white')


def switch_to_green():
    root.configure(bg='green')
    label.configure(text='PASE', bg='green', fg='white')
    root.after(2000, root.destroy)
    global patente_detectado
    patente_detectado = False


def switch_to_orange():
    root.configure(bg='orange')
    label.configure(text='No se pudo leer la placa', bg='orange', fg='white')

def detectar_adulteracion(patente):
    # Patrón de la patente vieja: 3 letras y 3 números
    patron_viejo = r'^[A-Z]{3}\d{3}$'

    # Patrón de la patente nueva: 2 letras, 3 números y 2 letras
    patron_nuevo = r'^[A-Z]{2}\d{3}[A-Z]{2}$'

    # Verificar si la patente coincide con alguno de los patrones
    if re.match(patron_viejo, patente) or re.match(patron_nuevo, patente):
        return False  # No hay adulteraciones

    return True  # Se detectó adulteración


def on_enter_press():
    # Capturar la imagen
    ret, frame = cap.read()
    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        # Guardar la imagen en el archivo temporal
        cv2.imwrite(temp_file.name, frame)

        # Obtener la ruta del archivo temporal
        foto = temp_file.name

    # Llamar a la función leer placa
    data = leer_placa(foto)
    print(data)

    if data is not None and len(data.get('results', [])) > 0:
        # Obtener la primera placa detectada
        plate = data['results'][0]['plate']

        # Genera un UUID
        my_uuid = str(uuid.uuid4())
        print(my_uuid)

        # Guardar la imagen con el nombre de la placa obtenido de la función leer_placa()
        foto = my_uuid + "-" + plate + ".jpg"
        # Determina la ruta de en mismo lugar
        ruta_guardado = r"C:\xampp\htdocs\phpPrueba\fotos"
        # Verifica si existe la carpeta
        if not os.path.exists(ruta_guardado):
            # Crea la carpeta
            os.makedirs(ruta_guardado)
        # Toma la ruta y la foto
        ruta_foto = os.path.join(ruta_guardado, foto)
        cv2.imwrite(ruta_foto, frame)
        adulterado = detectar_adulteracion(plate)
        subir_basededatos(data, 5, foto)  # Ejemplo: validar con un máximo de 5 placas
        switch_to_green()  # Cambiar a verde después de procesar correctamente la placa
    else:
        switch_to_orange()

#Camara
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
patente_detectado = False

while not patente_detectado:
    # Capturar la imagen
    ret, frame = cap.read()
    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        # Guardar la imagen en el archivo temporal
        cv2.imwrite(temp_file.name, frame)

        # Obtener la ruta del archivo temporal
        foto = temp_file.name

    data = leer_placa(foto)
    print(data)

    if len(data.get('results', [])) > 0:
        patente_detectado = True
        estado_pantalla = 'rojo'  # Estado inicial de la pantalla

        root = tk.Tk()
        root.attributes('-fullscreen', True)

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        label = tk.Label(root, font=('Helvetica', 30), fg='white')
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        switch_to_red()  # Establecer el color inicial en rojo
        root.after(3000, on_enter_press)
        root.mainloop()

cap.release()
cv2.destroyAllWindows()