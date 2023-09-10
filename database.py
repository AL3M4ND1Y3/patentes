import mysql.connector as db
import json
from datetime import datetime

def subir_basededatos(foto_patente, license_plate):
    global nuevo_valor
    nuevo_valor = 0
    with open('config.json') as database_file:
        keys = json.load(database_file)

    # Crear conexión a la base de datos
    conex = db.connect(
        host=keys["host"],  
        user=keys["user"],
        password=keys["password"],
        database=keys["database"],
        port=keys["port"]
    )

    parqueadero = keys["nombre"]
    cursor = conex.cursor()
    query = "SELECT id,espacios_ocupados FROM parqueaderos WHERE nombre = %s;"
    cursor.execute(query, (parqueadero,))
    result1 = cursor.fetchone()
    print(result1)
    parqueadero_id = result1[0]
    espacio = result1[1]
    print(espacio)

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
                query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
                cursor.execute(query, (vehiculo_id, parqueadero_id ,fecha_hora, foto_patente))
                conex.commit()
                nuevo_valor = espacio + 1
            elif hora_entrada and not hora_salida:
                # Si el vehículo ya tiene entrada y no tiene salida, se agrega como salida con la foto correspondiente
                fecha_hora = datetime.now()
                query = "UPDATE registros_entradas_salidas SET fecha_salida = %s WHERE vehiculo_id = %s AND fecha_entrada = %s"
                cursor.execute(query, (fecha_hora, vehiculo_id, hora_entrada))
                conex.commit()
                nuevo_valor = espacio - 1
            else:
                # Si el vehículo no tiene entrada o ya tiene entrada y salida, se agrega como entrada
                fecha_hora = datetime.now()
                query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
                cursor.execute(query, (vehiculo_id, parqueadero_id,fecha_hora, foto_patente))
                conex.commit()
                nuevo_valor = espacio + 1
        else:
            # El vehículo no tiene entradas ni salidas registradas, se agrega como entrada
            fecha_hora = datetime.now()
            query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
            cursor.execute(query, (vehiculo_id, parqueadero_id ,fecha_hora, foto_patente))
            conex.commit()
            nuevo_valor = espacio + 1
    else:
        # La placa no existe en la tabla "vehiculos"
        fecha_hora = datetime.now()
        query = "INSERT INTO vehiculos (placa, tipo_vehiculo_id,color_id,marca_id,modelo_id) VALUES (%s,1,1,2,1)"
        cursor.execute(query, (license_plate,))
        vehiculo_id = cursor.lastrowid  # Obtener el ID del vehículo recién insertado
        conex.commit()

        # Insertar en la tabla "registros_entradas_salidas" con el ID del vehículo recién insertado
        query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
        cursor.execute(query, (vehiculo_id, parqueadero_id,fecha_hora, foto_patente))
        conex.commit()
        nuevo_valor = espacio + 1

    print(nuevo_valor)
    query = "UPDATE parqueaderos SET espacios_ocupados = %s WHERE  nombre = %s"
    cursor.execute(query, (nuevo_valor,parqueadero))
    conex.commit() 

    # Cerrar conexión a la base de datos
    try:
        cursor.close()
    except:
        pass
    finally:
        conex.close()
    return True