# archivo: main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from PIL import Image
import io
import uvicorn
import os

# Crear app FastAPI
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Directorio de plantillas HTML
templates = Jinja2Templates(directory="templates")

# Cargar modelo
modelo_json_path = "Modelo train v2/senales_trafico_modelo.json"
weights_path = "Modelo train v2/senales_trafico_weights.weights.h5"

with open(modelo_json_path, "r") as json_file:
    model_json = json_file.read()

modelo_cargado = tf.keras.models.model_from_json(model_json)
modelo_cargado.load_weights(weights_path)
modelo_cargado.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Diccionario de clases
clases_dict = {
    1: 'Límite de velocidad (20 km/h)',
    2: 'Límite de velocidad (30 km/h)',
    3: 'Límite de velocidad (50 km/h)',
    4: 'Límite de velocidad (60 km/h)',
    5: 'Límite de velocidad (70 km/h)',
    6: 'Límite de velocidad (80 km/h)',
    7: 'Fin del límite de velocidad (80 km/h)',
    8: 'Límite de velocidad (100 km/h)',
    9: 'Límite de velocidad (120 km/h)',
    10: 'Prohibido adelantar',
    11: 'Prohibido adelantar vehículos de más de 3.5 toneladas',
    12: 'Prioridad en la intersección',
    13: 'Carretera prioritaria',
    14: 'Ceda el paso',
    15: 'Alto (Stop)',
    16: 'Prohibido el paso a vehículos',
    17: 'Prohibido vehículos de más de 3.5 toneladas',
    18: 'Prohibida la entrada',
    19: 'Precaución general',
    20: 'Curva peligrosa a la izquierda',
    21: 'Curva peligrosa a la derecha',
    22: 'Doble curva',
    23: 'Camino con baches',
    24: 'Carretera resbaladiza',
    25: 'Estrechamiento de la calzada por la derecha',
    26: 'Trabajos en la carretera',
    27: 'Semáforo',
    28: 'Paso de peatones',
    29: 'Zona escolar (cruce de niños)',
    30: 'Cruce de bicicletas',
    31: 'Precaución por hielo/nieve',
    32: 'Cruce de animales salvajes',
    33: 'Fin de los límites de velocidad y adelantamiento',
    34: 'Gire a la derecha más adelante',
    35: 'Gire a la izquierda más adelante',
    36: 'Solo recto',
    37: 'Siga recto o gire a la derecha',
    38: 'Siga recto o gire a la izquierda',
    39: 'Manténgase a la derecha',
    40: 'Manténgase a la izquierda',
    41: 'Glorieta obligatoria',
    42: 'Fin de la prohibición de adelantar',
    43: 'Fin de la prohibición de adelantar vehículos de más de 3.5 toneladas'
}

# Ruta principal para mostrar el HTML
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta de predicción simple
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img = img.resize((30, 30))
        x = np.array(img) / 255.0
        x = np.expand_dims(x, axis=0)

        prediccion = modelo_cargado.predict(x)
        indice_clase = np.argmax(prediccion)
        nombre_clase = clases_dict.get(indice_clase + 1, "Clase desconocida")

        return {"prediction": nombre_clase}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")

# Ruta de predicción con confianza
@app.post("/predict/realtime/")
async def predict_realtime(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img = img.resize((30, 30))
        x = np.array(img) / 255.0
        x = np.expand_dims(x, axis=0)

        prediccion = modelo_cargado.predict(x)
        indice_clase = int(np.argmax(prediccion))
        confianza = float(np.max(prediccion)) * 100
        nombre_clase = clases_dict.get(indice_clase + 1, "Clase desconocida")

        return {
            "id": indice_clase + 1,
            "nombre": nombre_clase,
            "confianza": round(confianza, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en tiempo real: {str(e)}")

# Ejecutar en modo local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render define PORT automáticamente
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
