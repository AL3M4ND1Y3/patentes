from mysql.connector import pooling
import json
from datetime import datetime,timedelta
import os
from dotenv import load_dotenv

load_dotenv()


# Abrir conexión a la base de datos al comienzo de tu script
""" with open('config.ini') as database_file:
    keys = json.load(database_file) """

# Configurar el diccionario dbconfig con el nombre y el tamaño del pool
dbconfig = {
    "host": os.environ.get('DATABASE_HOST'),
    "user": os.environ.get('DATABASE_USER'),
    "password": os.environ.get('DATABASE_PASSWORD'),
    "database": os.environ.get('DATABASE_database'),
    "port": os.environ.get('DATABASE_PORT'),
    "pool_name": "DB-POOL",
    "pool_size": 8
} 

# Crear el pool de conexiones
db_pool = pooling.MySQLConnectionPool(**dbconfig)

        
def obtener_vehiculoID(license_plate):
    conex = db_pool.get_connection()
    # Crear un cursor
    cursor = conex.cursor()
    # Verificar si la placa ya está registrada en la tabla "vehiculos"
    query = "SELECT id FROM vehiculos WHERE placa = %s"
    cursor.execute(query, (license_plate,))
    result = cursor.fetchone()

    if result:
        # Si se encuentra un resultado, devolver el ID como un entero
        return result[0]
    else:
        try:
            query = "INSERT INTO vehiculos (placa, tipo_vehiculo_id, color_id, marca_id, modelo_id) VALUES (%s, 1, 1, 2, 1)"
            cursor.execute(query, (license_plate,))
            conex.commit()
            vehiculo_id = cursor.lastrowid  # Obtener el ID del vehículo recién insertado
            return vehiculo_id
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al insertar el registro
            print("Error al insertar vehículo:", str(e))
            return None
        finally:
            conex.close()



def obtener_username(placa):
    conex = db_pool.get_connection()
    # Crear un cursor
    cursor = conex.cursor()

    query = """
        SELECT users.name
        FROM vehiculos
        INNER JOIN vehiculos_users ON vehiculos.id = vehiculos_users.vehiculo_id
        INNER JOIN users ON vehiculos_users.user_id = users.id
        WHERE vehiculos.placa = %s;
        """
    cursor.execute(query, (placa,))
    result = cursor.fetchone()
    print(result)
    
    if result is None:
        return "Bienvenido, Unanse a nuestra familia descargandose la Aplicacion 'Likin Parking'"
    elif len(result) == 0:
        return "Bienvenido, Unanse a nuestra familia descargandose la Aplicacion 'Linkin Parking'"
    else:
        return "Bienvenido " + result[0]



def subir_basededatos(foto_patente, license_plate):
    conex = db_pool.get_connection()
    try:
        cursor = conex.cursor()
        global nuevo_valor
        nuevo_valor = 0
        parqueadero = os.environ.get('DATABASE_nombre')
        query = "SELECT id, capacidad FROM parqueaderos WHERE nombre = %s;"
        cursor.execute(query, (parqueadero,))
        result = cursor.fetchone()
        print(result)
        parqueadero_id, espacio = result
        print(espacio)

        if result:
            # La placa existe en la tabla "vehiculos"
            vehiculo_id = obtener_vehiculoID(license_plate)  # Obtener el ID del vehículo

            # Verificar si el vehículo ya tiene una entrada sin salida
            query = "SELECT fecha_entrada, fecha_salida FROM registros_entradas_salidas WHERE vehiculo_id = %s ORDER BY fecha_entrada DESC LIMIT 1"
            cursor.execute(query, (vehiculo_id,))
            result = cursor.fetchone()

            if result:
                hora_entrada, hora_salida = result
                if hora_entrada and not hora_salida:
                    # Si el vehículo tiene una entrada sin salida
                    hora_actual = datetime.now()
                    tiempo_transcurrido = hora_actual - hora_entrada
                    if tiempo_transcurrido < timedelta(minutes=15):
                        # No permitir una nueva entrada si han pasado menos de 15 minutos
                        return False
                    else:
                        return True
            else:
                # El vehículo no tiene entradas ni salidas registradas, se agrega como entrada
                fecha_hora = datetime.now()
                query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
                cursor.execute(query, (vehiculo_id, parqueadero_id ,fecha_hora, foto_patente))
                conex.commit()
                nuevo_valor = espacio - 1
        else:
            # La placa no existe en la tabla "vehiculos"
            fecha_hora = datetime.now()
            query = "INSERT INTO vehiculos (placa, tipo_vehiculo_id, color_id, marca_id, modelo_id) VALUES (%s, 1, 1, 2, 1)"
            cursor.execute(query, (license_plate,))
            vehiculo_id = cursor.lastrowid  # Obtener el ID del vehículo recién insertado
            conex.commit()

            # Insertar en la tabla "registros_entradas_salidas" con el ID del vehículo recién insertado
            query = "INSERT INTO registros_entradas_salidas (vehiculo_id, parqueadero_id, espacio_estacionamiento_id, fecha_entrada, foto_entrada, precio) VALUES (%s, %s, 1, %s, %s, 0)"
            cursor.execute(query, (vehiculo_id, parqueadero_id, fecha_hora, foto_patente))
            conex.commit()
            nuevo_valor = espacio - 1

        print(nuevo_valor)
        query = "UPDATE parqueaderos SET capacidad = %s WHERE nombre = %s"
        cursor.execute(query, (nuevo_valor, parqueadero))
        conex.commit()
        return True
    finally:
        conex.close()

