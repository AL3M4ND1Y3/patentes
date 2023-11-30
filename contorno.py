import cv2

def es_patente_valida(contorno, ancho_min=100, ancho_max=300, alto_min=50, alto_max=150, aspect_ratio_min=2, aspect_ratio_max=4):
    x, y, w, h = cv2.boundingRect(contorno)

    # Calcular la relación de aspecto
    aspect_ratio = w / float(h)

    # Verificar si las dimensiones y la relación de aspecto están dentro del rango
    if ancho_min <= w <= ancho_max and alto_min <= h <= alto_max and aspect_ratio_min <= aspect_ratio <= aspect_ratio_max:
        return True  # Se considera una placa válida
    else:
        return False

def detectar_contorno_patente(frame):
    # Convertir el fotograma a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Aplicar un filtro Gaussiano para reducir el ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Aplicar la detección de bordes utilizando el operador Canny
    edges = cv2.Canny(blurred, 50, 150)

    # Buscar contornos en la imagen de bordes
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Definir criterios adicionales para considerar como placa de patente
    min_area = 2000
    aspect_ratio_min = 2
    aspect_ratio_max = 4

    patente_detectada = False  # Bandera para indicar si se detecta una patente

    # Dibujar el contorno de la placa de patente en el fotograma original
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area and es_patente_valida(contour, aspect_ratio_min=aspect_ratio_min, aspect_ratio_max=aspect_ratio_max):
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            patente_detectada = True  # Se detectó una placa
            break

    # Mostrar el fotograma con el contorno de la placa de patente resaltado
    cv2.imshow('Detección de Placa de Patente', frame)

    # Capturar la tecla presionada
    key = cv2.waitKey(1)

    # Verificar si se presionó la tecla 'q'
    if key == ord('q'):
        cv2.destroyAllWindows()

    # Devolver True cuando se detecta una placa
    return patente_detectada, frame
