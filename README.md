# CyberMariscos - Tests automatizados del frontend de Bettson (Malackathon)
![Image](.github/lets-go-gambling.gif)

## Componentes
### Visión por Computador
`coords.py` es el módulo de detección de botones, es usado para detectar las coordenadas de cualquier botón que pueda avanzar el juego, a partir de bytes del canvas. Usa `opencv`.

### Reconocimiento Óptico de Caracteres
`text.py` es el módulo de extracción de texto, es usado para obtener el coste de una tirada desde bytes de un canvas.
Usa la librería `pytesseract` y una expresión regular para ello.

### Simulación de usuario
`main.py` es el componente principal, dependiente del resto ya descritos.

Usa la librería `playwright` + `seleniumbase` en su modo Stealthy para poder evitar problemas de autentificación debido a Cloudfront.

### Tests mock
`report.py` ejecuta tests mock usando capturas de pantalla elegidas anteriormente (encontradas en `./examples`).

## Flujo de funcionamiento
1. El navegador se inicia y accede a `https://www.betsson.es`.
2. Inicia sesión con las credenciales dadas.
    * Si hay algún popup (como el de las keyrings o la de aceptar consentimiento) lo cierra / acepta
3. Guarda el balance inicial.
4. Elige un juego aleatorio de la lista "Casino".
5. El navegador accede a la página del juego.
6. Si hay algún mecanismo anti-adicción activo procede a hacer el flujo para continuar.
7. Inicia el juego
8. Cada 5 segundos, realiza una captura de pantalla del `iframe` y lo guarda en `./output`:
    * Intenta conseguir la siguiente acción (esperar, botón...)
        * Si hay, la ejecuta
    * Intenta conseguir el balance actual a partir del `iframe`
        * Si lo encuentra, intenta verificar que el valor es correcto
9. Al hacer 20 capturas de pantallas o fallar al conseguir la siguiente acción 5 veces seguidas se termina la ejecución
10. ??
11. Profit

Todas estas acciones son registradas en `output/app.log` y en el `STDOUT`.

## Instalación

<details>
<summary>Windows</summary>

```bash
python3 -m venv .venv
.\.venv\bin\Activate.ps1
pip install -r requirements.txt
```
</details>

<details>
<summary>Linux</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
</details>

También pueden ser necesarias instalar programas externos, como `tesseract-ocr`.

### Variables de entorno
En `.env.example` están las variables de entorno usadas en el programa.

| Key | Descripción |
| :--: | :--: |
| ACCOUNT_MONEY_EMAIL | Correo electrónico de usuario con dinero |
| ACCOUNT_MONEY_PASSWORD | Contraseña de usuario con dinero |
| ACCOUNT_BROKE_EMAIL | Correo electrónico de usuario muerto de hambre |
| ACCOUNT_BROKE_PASSWORD | Contraseña de usuario muerto de hambre |

## Ejecución
### Principal
```
$ python3 main.py -h
usage: GameTester [-h] [--headless] [-m]

Game checker for Betsson

options:
  -h, --help   show this help message and exit
  --headless   Run in headless mode
  -m, --money  Use account with money

Made with <3 (and energy drinks) by CyberMariscos
```

### Reporte
```bash
python3 report.py
```
