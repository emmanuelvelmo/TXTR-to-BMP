import struct # Interpretación de datos binarios (big-endian, little-endian)
import pathlib # Manejo moderno de rutas de archivos

# FUNCIONES
# Invierte el orden de los bits (2 bits) - equivalente a SwapBits en MaxScript
def swap_bits(val):
    b1 = val & 0x3 # Máscara binaria 00000011
    b2 = val & 0xC # Máscara binaria 00001100
    b3 = val & 0x30 # Máscara binaria 00110000
    b4 = val & 0xC0 # Máscara binaria 11000000
    
    return (b1 << 6) + (b2 << 2) + (b3 >> 2) + (b4 >> 6)

# Convierte color RGB565 (16 bits) a RGB888 (24 bits)
def rgb565_to_rgb(color565):
    r = ((color565 >> 11) & 0x1F) * 255 // 31 # Máscara binaria 00011111
    g = ((color565 >> 5) & 0x3F) * 255 // 63 # Máscara binaria 00111111
    b = (color565 & 0x1F) * 255 // 31 # Máscara binaria 00011111
    
    return (r, g, b)

# Decodifica un bloque CMPR de 8 bytes a 16 píxeles RGB
def decode_cmpr_block(block_data):
    # 1. Leer colores (big-endian)
    color0 = (block_data[0] << 8) | block_data[1]
    color1 = (block_data[2] << 8) | block_data[3]
    
    # 2. Convertir RGB565 a RGB888
    rgb0 = rgb565_to_rgb(color0)
    rgb1 = rgb565_to_rgb(color1)
    
    # 3. Calcular colores de mezcla
    colors = [
        rgb0, # 00 = Color0
        rgb1, # 01 = Color1
        tuple((2*rgb0[i] + rgb1[i]) // 3 for i in range(3)), # 10 = (2*C0 + C1)/3
        tuple((rgb0[i] + 2*rgb1[i]) // 3 for i in range(3)) # 11 = (C0 + 2*C1)/3
    ]
    
    # 4. Extraer índices de 2 bits (4 índices por byte)
    indices = []
    
    for byte in block_data[4:8]:
        for i in range(3, -1, -1): # De MSB a LSB
            idx = (byte >> (i * 2)) & 0x3 # Máscara binaria 00000011
            indices.append(idx)
    
    # 5. Construir matriz 4x4 de píxeles
    pixels = []
    
    for i in range(16):
        pixels.append(colors[indices[i]])
    
    return pixels

# Decodifica un mipmap completo a píxeles RGB
def decode_mipmap(data, width, height):
    blocks_per_row = width // 4
    blocks_per_col = height // 4
    
    # Crear array de píxeles (alto, ancho, 3)
    pixels = [[[0, 0, 0] for _ in range(width)] for _ in range(height)]
    
    s = 0
    
    # Recorrer en orden de GameCube (macrobloques de 2x2)
    for y in range(0, blocks_per_col, 2):
        for x in range(0, blocks_per_row, 2):
            for dy in range(2):
                for dx in range(2):
                    # Leer bloque de 8 bytes
                    block = data[s:s+8]
                    s += 8
                    
                    # Decodificar bloque
                    block_pixels = decode_cmpr_block(block)
                    
                    # Posición del bloque en la imagen
                    block_x = (x + dx) * 4
                    block_y = (y + dy) * 4
                    
                    # Colocar píxeles
                    for py in range(4):
                        for px in range(4):
                            pixel_idx = py * 4 + px
                            pixels[block_y + py][block_x + px] = block_pixels[pixel_idx]
    
    return pixels

# Crea el header BMP de 54 bytes
def create_bmp_header(width, height):
    # Tamaño total del archivo: header (54) + datos (width * height * 3)
    file_size = 54 + (width * height * 3)
    
    # Header BMP (54 bytes)
    header = bytearray(54)
    
    # Magic number "BM"
    header[0] = 0x42 # 'B'
    header[1] = 0x4D # 'M'
    
    # Tamaño total del archivo (little-endian)
    header[2] = file_size & 0xFF # Máscara binaria 11111111
    header[3] = (file_size >> 8) & 0xFF # Máscara binaria 11111111
    header[4] = (file_size >> 16) & 0xFF # Máscara binaria 11111111
    header[5] = (file_size >> 24) & 0xFF # Máscara binaria 11111111
    
    # Reservado (4 bytes)
    header[6] = 0
    header[7] = 0
    header[8] = 0
    header[9] = 0
    
    # Offset de los datos de píxeles (54 bytes)
    header[10] = 54
    header[11] = 0
    header[12] = 0
    header[13] = 0
    
    # Tamaño del header DIB (40 bytes)
    header[14] = 40
    header[15] = 0
    header[16] = 0
    header[17] = 0
    
    # Ancho (little-endian)
    header[18] = width & 0xFF # Máscara binaria 11111111
    header[19] = (width >> 8) & 0xFF # Máscara binaria 11111111
    header[20] = 0
    header[21] = 0
    
    # Alto (little-endian)
    header[22] = height & 0xFF # Máscara binaria 11111111
    header[23] = (height >> 8) & 0xFF # Máscara binaria 11111111
    header[24] = 0
    header[25] = 0
    
    # Planos (1)
    header[26] = 1
    header[27] = 0
    
    # Bits por píxel (24 = RGB)
    header[28] = 24
    header[29] = 0
    
    # Compresión (0 = sin comprimir)
    header[30] = 0
    header[31] = 0
    header[32] = 0
    header[33] = 0
    
    # Tamaño de los datos (width * height * 3)
    data_size = width * height * 3
    header[34] = data_size & 0xFF # Máscara binaria 11111111
    header[35] = (data_size >> 8) & 0xFF # Máscara binaria 11111111
    header[36] = (data_size >> 16) & 0xFF # Máscara binaria 11111111
    header[37] = (data_size >> 24) & 0xFF # Máscara binaria 11111111
    
    # Resolución (píxeles por metro, 0 = no especificado)
    header[38] = 0
    header[39] = 0
    header[40] = 0
    header[41] = 0
    header[42] = 0
    header[43] = 0
    header[44] = 0
    header[45] = 0
    
    # Colores en la paleta (0 = todos)
    header[46] = 0
    header[47] = 0
    header[48] = 0
    header[49] = 0
    
    # Colores importantes (0 = todos)
    header[50] = 0
    header[51] = 0
    header[52] = 0
    header[53] = 0
    
    return header

# Convierte un archivo TXTR a BMP
def txtr_to_bmp(input_path, output_path):
    with open(input_path, 'rb') as f:
        # Leer encabezado TXTR (12 bytes, big-endian)
        header = f.read(12)
        
        if len(header) < 12:
            return False
        
        txformat = struct.unpack('>I', header[0:4])[0]
        width = struct.unpack('>H', header[4:6])[0]
        height = struct.unpack('>H', header[6:8])[0]
        
        # Verificar formato
        if txformat != 0xA:
            return False
        
        # Leer solo el primer mipmap (el de mayor resolución)
        mipmap_size = (width * height) // 2
        data = f.read(mipmap_size)
        
        if len(data) < mipmap_size:
            return False
        
        # Decodificar el mipmap
        pixels = decode_mipmap(data, width, height)
        
        # Crear header BMP
        bmp_header = create_bmp_header(width, height)
        
        # Escribir archivo BMP
        with open(output_path, 'wb') as out:
            # Escribir header
            out.write(bmp_header)
            
            # Escribir píxeles (BGR orden, filas de abajo hacia arriba)
            # BMP guarda los píxeles en orden BGR y de abajo hacia arriba
            for y in range(height - 1, -1, -1): # De abajo hacia arriba
                for x in range(width):
                    r, g, b = pixels[y][x]
                    
                    # BMP usa orden BGR
                    out.write(bytes([b, g, r]))
        
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
    output_path = ruta_path.parent / (ruta_path.stem + ".bmp")
    
    # Mostrar separador visual para inicio de resultados
    print("-" * 36)
    
    # Convertir archivo
    if txtr_to_bmp(ruta_path, output_path):
        print("File processed")
    else:
        print("Conversion failed")
    
    # Mostrar separador final
    print("-" * 36 + "\n")
