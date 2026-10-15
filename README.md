# CyberMariscos - Tests automatizados del frontend de Bettson (Malackathon)

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

## Ejecución de tests

```bash
python3 report.py
```

## Funcionamiento

`text.py` es el módulo de extracción de texto, es usado para obtener el coste de una tirada desde bytes de un canvas.
Usa la librería `pytesseract` y una expresión regular para ello.

`coords.py` es el módulo de detección de botones, es usado para detectar las coordenadas de cualquier botón que pueda avanzar el juego, a partir de bytes del canvas. Usa `opencv`
