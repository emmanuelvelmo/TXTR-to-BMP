import struct # Interpretación de datos binarios (big-endian, little-endian)
import pathlib # Manejo moderno de rutas de archivos

# FUNCIONES
# Invierte el orden de los bits (2 bits). Útil en DDS
def cambiar_bits(bits_val):
    par_0 = bits_val & 0x3 # Máscara binaria 00000011
    par_1 = bits_val & 0xC # Máscara binaria 00001100
    par_2 = bits_val & 0x30 # Máscara binaria 00110000
    par_3 = bits_val & 0xC0 # Máscara binaria 11000000
    
    return (par_0 << 6) + (par_1 << 2) + (par_2 >> 2) + (par_3 >> 6) # Reubicar cada par de bits en orden inverso

# Crea el header BMP de 54 bytes
def crear_header_bmp(ancho_val, alto_val):
    # Tamaño total del archivo: header (54) + datos (ancho_val * alto_val * 3)
    tamano_archivo = 54 + (ancho_val * alto_val * 3)
    
    # Header BMP (54 bytes)
    header_bmp = bytearray(54)
    
    # Magic number "BM"
    header_bmp[0] = 0x42 # 'B'
    header_bmp[1] = 0x4D # 'M'
    
    # Tamaño total del archivo (little-endian)
    header_bmp[2] = tamano_archivo & 0xFF # Máscara binaria 11111111
    header_bmp[3] = (tamano_archivo >> 8) & 0xFF # Máscara binaria 11111111
    header_bmp[4] = (tamano_archivo >> 16) & 0xFF # Máscara binaria 11111111
    header_bmp[5] = (tamano_archivo >> 24) & 0xFF # Máscara binaria 11111111
    
    # Reservado (4 bytes)
    header_bmp[6] = 0
    header_bmp[7] = 0
    header_bmp[8] = 0
    header_bmp[9] = 0
    
    # Offset de los datos de píxeles (54 bytes)
    header_bmp[10] = 54
    header_bmp[11] = 0
    header_bmp[12] = 0
    header_bmp[13] = 0
    
    # Tamaño del header DIB (40 bytes)
    header_bmp[14] = 40
    header_bmp[15] = 0
    header_bmp[16] = 0
    header_bmp[17] = 0
    
    # Ancho (little-endian)
    header_bmp[18] = ancho_val & 0xFF # Máscara binaria 11111111
    header_bmp[19] = (ancho_val >> 8) & 0xFF # Máscara binaria 11111111
    header_bmp[20] = 0
    header_bmp[21] = 0
    
    # Alto (little-endian)
    header_bmp[22] = alto_val & 0xFF # Máscara binaria 11111111
    header_bmp[23] = (alto_val >> 8) & 0xFF # Máscara binaria 11111111
    header_bmp[24] = 0
    header_bmp[25] = 0
    
    # Planos (1)
    header_bmp[26] = 1
    header_bmp[27] = 0
    
    # Bits por píxel (24 = RGB)
    header_bmp[28] = 24
    header_bmp[29] = 0
    
    # Compresión (0 = sin comprimir)
    header_bmp[30] = 0
    header_bmp[31] = 0
    header_bmp[32] = 0
    header_bmp[33] = 0
    
    # Tamaño de los datos (ancho_val * alto_val * 3)
    tamano_datos = ancho_val * alto_val * 3
  
    header_bmp[34] = tamano_datos & 0xFF # Máscara binaria 11111111
    header_bmp[35] = (tamano_datos >> 8) & 0xFF # Máscara binaria 11111111
    header_bmp[36] = (tamano_datos >> 16) & 0xFF # Máscara binaria 11111111
    header_bmp[37] = (tamano_datos >> 24) & 0xFF # Máscara binaria 11111111
    
    # Resolución (píxeles por metro, 0 = no especificado)
    header_bmp[38] = 0
    header_bmp[39] = 0
    header_bmp[40] = 0
    header_bmp[41] = 0
    header_bmp[42] = 0
    header_bmp[43] = 0
    header_bmp[44] = 0
    header_bmp[45] = 0
    
    # Colores en la paleta (0 = todos)
    header_bmp[46] = 0
    header_bmp[47] = 0
    header_bmp[48] = 0
    header_bmp[49] = 0
    
    # Colores importantes (0 = todos)
    header_bmp[50] = 0
    header_bmp[51] = 0
    header_bmp[52] = 0
    header_bmp[53] = 0
    
    return header_bmp

# Convierte color RGB565 (16 bits) a RGB888 (24 bits)
def color_565_a_rgb(color_565):
    rojo_val = ((color_565 >> 11) & 0x1F) * 255 // 31 # Máscara binaria 00011111
    verde_val = ((color_565 >> 5) & 0x3F) * 255 // 63 # Máscara binaria 00111111
    azul_val = (color_565 & 0x1F) * 255 // 31 # Máscara binaria 00011111
    
    return (rojo_val, verde_val, azul_val)

# Decodifica un bloque CMPR de 8 bytes a 16 píxeles RGB
def decodificar_bloque_cmpr(bloque_datos):
    # 1. Leer colores (big-endian)
    color_0 = (bloque_datos[0] << 8) | bloque_datos[1] # Juntar ambos bytes
    color_1 = (bloque_datos[2] << 8) | bloque_datos[3]
    
    # 2. Convertir RGB565 a RGB888
    rgb_0 = color_565_a_rgb(color_0)
    rgb_1 = color_565_a_rgb(color_1)
    
    # 3. Calcular colores de mezcla (Combinaciones en capas RGB)
    colores_lista = [
        rgb_0, # 00 = Color0
        rgb_1, # 01 = Color1
        tuple((2*rgb_0[indice_val] + rgb_1[indice_val]) // 3 for indice_val in range(3)), # 10 = (2*C0 + C1)/3
        tuple((rgb_0[indice_val] + 2*rgb_1[indice_val]) // 3 for indice_val in range(3)) # 11 = (C0 + 2*C1)/3
    ]
    
    # 4. Extraer índices de 2 bits (4 índices por byte)
    indices_lista = []
    
    for byte_val in bloque_datos[4:8]: # Recorre byte a byte
        for bit_pos in range(3, -1, -1): # De MSB a LSB
            indice_val = (byte_val >> (bit_pos * 2)) & 0x3 # Máscara binaria 00000011
            indices_lista.append(indice_val)
    
    # 5. Construir matriz 4x4 de píxeles
    pixeles_lista = []
    
    for indice_val in range(16):
        pixeles_lista.append(colores_lista[indices_lista[indice_val]])
    
    return pixeles_lista

# Decodifica un mipmap completo a píxeles RGB
def decodificar_mipmap(datos_val, ancho_val, alto_val):
    bloques_por_fila = ancho_val // 4
    bloques_por_columna = alto_val // 4
    
    # Crear array de píxeles (alto, ancho, 3)
    pixeles_matriz = [[[0, 0, 0] for _ in range(ancho_val)] for _ in range(alto_val)]
    
    posicion_val = 0
    
    # Recorrer en orden macrobloques de 2x2
    for y_val in range(0, bloques_por_columna, 2):
        for x_val in range(0, bloques_por_fila, 2):
            for dy_val in range(2):
                for dx_val in range(2):
                    # Leer bloque de 8 bytes
                    bloque_val = datos_val[posicion_val:posicion_val+8]
                    posicion_val += 8
                    
                    # Decodificar bloque
                    pixeles_bloque = decodificar_bloque_cmpr(bloque_val)
                    
                    # Posición del bloque en la imagen
                    bloque_x = (x_val + dx_val) * 4
                    bloque_y = (y_val + dy_val) * 4
                    
                    # Colocar píxeles
                    for py_val in range(4):
                        for px_val in range(4):
                            pixel_idx = (py_val * 4) + px_val
                            pixeles_matriz[bloque_y + py_val][bloque_x + px_val] = pixeles_bloque[pixel_idx]
    
    return pixeles_matriz

# Convierte un archivo TXTR a BMP
def txtr_a_bmp(ruta_entrada, ruta_salida):
    with open(ruta_entrada, 'rb') as f:
        # Leer encabezado TXTR (12 bytes, big-endian)
        header_val = f.read(12)
        
        if len(header_val) < 12:
            return False
        
        formato_tx = struct.unpack('>I', header_val[0:4])[0]
        ancho_val = struct.unpack('>H', header_val[4:6])[0]
        alto_val = struct.unpack('>H', header_val[6:8])[0]
        mipmaps_val = struct.unpack('>I', header_val[8:12])
        
        # Verificar formato
        if formato_tx != 0xA:
            return False
        
        # Leer solo el primer mipmap (el de mayor resolución)
        tamano_mipmap = (ancho_val * alto_val) // 2
        datos_val = f.read(tamano_mipmap)
        
        if len(datos_val) < tamano_mipmap:
            return False
        
        # Decodificar el mipmap
        pixeles_matriz = decodificar_mipmap(datos_val, ancho_val, alto_val)
        
        # Crear header BMP
        header_bmp = crear_header_bmp(ancho_val, alto_val)
        
        # Escribir archivo BMP
        with open(ruta_salida, 'wb') as out:
            # Escribir header
            out.write(header_bmp)
            
            # Escribir píxeles (BGR orden, filas de abajo hacia arriba). BMP guarda los píxeles en orden BGR y de abajo hacia arriba
            for y_val in range(alto_val - 1, -1, -1): # De abajo hacia arriba
                for x_val in range(ancho_val):
                    rojo_val, verde_val, azul_val = pixeles_matriz[y_val][x_val]
                    
                    # BMP usa orden BGR
                    out.write(bytes([azul_val, verde_val, rojo_val]))
        
        return True

# PUNTO DE PARTIDA
while True:
    # Solicitar ruta de archivo
    ruta_entrada = input("Enter TXTR file directory: ").strip('"\'')
    ruta_path = pathlib.Path(ruta_entrada)
    
    # Verificar que la ruta exista y sea un archivo
    if not ruta_path.exists() or not ruta_path.is_file():
        print("Wrong directory\n")
        
        continue
    
    # Generar ruta de salida
    ruta_salida = ruta_path.parent / (ruta_path.stem + ".bmp")
    
    # Mostrar separador visual para inicio de resultados
    print("-" * 36)
    
    # Convertir archivo
    if txtr_a_bmp(ruta_path, ruta_salida):
        print("File processed")
    else:
        print("Conversion failed")
    
    # Mostrar separador final
    print("-" * 36 + "\n")
