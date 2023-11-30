from configparser import ConfigParser
import cv2

print("---------Opciones--------")
print("1- Cambiar la Camara")
print("2- Asignar Nombre de Parqueadero/Estacionamiento")

def obtener_numero_camara():
    config = ConfigParser()
    config.read('config.ini')
    return config.getint('Configuracion', 'NumeroCamara', fallback=0)

def cambiar_numero_camara(nuevo_numero_camara):
    config = ConfigParser()
    config.read('config.ini')
    config.set('Configuracion', 'NumeroCamara', str(nuevo_numero_camara))
    
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def obtener_nombres_camaras_disponibles():
    nombres_camaras = []

    for i in range(20):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Intentamos obtener el nombre con diferentes propiedades
            nombre = cap.get(cv2.CAP_PROP_FOURCC)
            if nombre:
                nombre = str(nombre)
            else:
                nombre = "Desconocido"
            
            nombres_camaras.append((i, nombre))
            cap.release()

    return nombres_camaras

def obtener_lista_camaras_disponibles():
    lista_camaras = [i for i in range(20) if cv2.VideoCapture(i).isOpened()]
    return lista_camaras

def mostrar_menu_cambiar_camara():
    print("Cámaras disponibles:")
    nombres_camaras = obtener_nombres_camaras_disponibles()
    for i, (camara, nombre) in enumerate(nombres_camaras):
        print(f"{i}: Cámara {camara} - Nombre: {nombre}")

    camara_actual = obtener_numero_camara()
    print(f"La cámara actual es: Cámara {camara_actual}")

    while True:
        try:
            camara_seleccionada = int(input("Seleccione la nueva cámara (número): "))
            if camara_seleccionada in [camara for camara, _ in nombres_camaras]:
                cambiar_numero_camara(camara_seleccionada)
                print("¡Cámara cambiada exitosamente!")
                break
            else:
                print("Número de cámara no válido. Intente de nuevo.")
        except ValueError:
            print("Por favor, ingrese un número válido.")


def crear_archivo():
    

opcion = input("Ingrese la opción deseada : ")

if opcion == '1':   
    mostrar_menu_cambiar_camara()
elif opcion == '2':
    # Lógica para la opción 2
    pass
else:
    print("Opción no válida.")
