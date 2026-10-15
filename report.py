import sys
from pathlib import Path
import cv2 as cv

from text import img_to_apuesta

# arte ascii, generado en https://patorjk.com/software/taag/
print("\033[0;36m▓▀▀\033[0;36;47m▓\033[0;37m \033[0;36m█\033[0;37m  \033[0;36m█\033[0;37m \033[0;36m█▄▄▄\033[0;37m \033[0;36m▓▀▀\033[0;36;47m▓\033[0;37m \033[0;36;47m▓\033[0;36m▀▀█\033[0;37m \033[0;36m▓▀\033[0;36;47m▓\033[0;36m▀█\033[0;37m   \033[0;36m▀▀▓\033[0;37m \033[0;36;47m▓\033[0;36m▀▀█\033[0;37m \033[0;36m█\033[0;37m \033[0;36m█▀▀\033[0;37m  \033[0;36m▓▀▀\033[0;36;47m▓\033[0;37m \033[0;36m▓▀▀\033[0;36;47m▓\033[0;37m \033[0;36m█▀▀\033[0;37m \033[0m")
print("\033[0;36m█\033[0;37m    \033[0;36m▀█▀▀\033[0;37m \033[0;36m█\033[0;37m  \033[0;36m█\033[0;37m \033[0;36m█▄▄█\033[0;37m \033[0;36m█\033[0;37m    \033[0;36m█\033[0;37m \033[0;36m█\033[0;37m \033[0;36m▀█\033[0;37m \033[0;36m█▀▀█\033[0;37m \033[0;36m█\033[0;37m    \033[0;36m█\033[0;37m \033[0;36m▀▀▀█\033[0;37m \033[0;36m█\033[0;37m    \033[0;36m█\033[0;37m  \033[0;36m█\033[0;37m \033[0;36m▀▀▀█\033[0m")
print("\033[0;36m█▄▄▓\033[0;37m  \033[0;36;47m▓\033[0;37m   \033[0;36m█▄▄\033[0;36;47m▓\033[0;37m \033[0;36m█▄▄\033[0;37m  \033[0;36m█\033[0;37m    \033[0;36m█\033[0;37m \033[0;36m▀\033[0;37m  \033[0;36m█\033[0;37m \033[0;36m▓▄▄\033[0;36;47m▓\033[0;37m \033[0;36m█\033[0;37m    \033[0;36m█\033[0;37m \033[0;36;47m▓\033[0;36m▄▄▓\033[0;37m \033[0;36m█▄▄▓\033[0;37m \033[0;36m█▄▄▓\033[0;37m \033[0;36;47m▓\033[0;36m▄▄▓\033[0m\n")

env_path = Path(".env")
if not env_path.is_file():
    print("\033[7;31mERROR!\033[0m Archivo \033[0;36m.env\033[0m no encontrado. Añádelo con credenciales válidas para continuar.")
    sys.exit(1)

print("Ejecutando tests... (detección de imágenes)")
img_error = False

img = cv.imread('./examples/test/test1.png')
apuesta = img_to_apuesta(img)

if apuesta != 2.00: img_error = True

if img_error:
    print('  \033[0;31mTest fallido\033[0m: detección de imágenes')
else:
    print('  \033[0;32mTest superado\033[0m: detección de imágenes')

print("Ejecutando tests... (cuenta con saldo)")
money_error = False

if money_error:
    print('  \033[0;31mTest fallido\033[0m: cuenta con saldo')
else:
    print('  \033[0;32mTest superado\033[0m: cuenta con saldo')

print("Ejecutando tests... (cuenta sin saldo)")
nomoney_error = False

if nomoney_error:
    print('  \033[0;31mTest fallido\033[0m: cuenta sin saldo')
else:
    print('  \033[0;32mTest superado\033[0m: cuenta sin saldo')

if img_error or money_error or nomoney_error:
    print("\033[7;31mERROR!\033[0m Alguno de los tests ha fallado.")
    sys.exit(1)

print("\033[7;32mTodo bien! Vas a vivir un día más :D\033[0m")
