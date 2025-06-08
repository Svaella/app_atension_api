import os
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from typing import Union

# 🎯 Conexión a BD
#DATABASE_URL = "postgresql://postgres:Svaella10.@localhost:5432/atension_db" // local
DATABASE_URL = "postgresql://postgres:Svaella10.@35.247.77.11:5432/atension_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 🎯 Tabla
class HTARegistro(Base):
    __tablename__ = "hta_registros"
    id = Column(Integer, primary_key=True, index=True)
    sexo = Column(String(10), nullable=False)
    edad = Column(Integer, nullable=False)
    peso = Column(Numeric(5, 2), nullable=False)
    altura = Column(Numeric(5, 2), nullable=False)
    bmi = Column(Numeric(5, 2), nullable=False)
    frutas = Column(String(5), nullable=False)
    vegetales = Column(String(5), nullable=False)
    sal = Column(String(5), nullable=False)
    alcohol = Column(String(5), nullable=False)
    tabaco = Column(String(30), nullable=False)
    vapeo = Column(String(30), nullable=False)
    estres_dias = Column(Integer, nullable=False)
    actividad = Column(String(5), nullable=False)
    colesterol = Column(String(5), nullable=False)
    diabetes = Column(String(30), nullable=False)
    diagnosticado_hta = Column(String(5), nullable=False)  # ✅ Texto
    riesgo = Column(String(10), nullable=False)
    probabilidad = Column(Numeric(5, 2), nullable=False)
    puntaje_conocimiento_hta = Column(Integer)
    respuestas_hta = Column(String)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

# Crear la tabla si no existe
Base.metadata.create_all(bind=engine)

app = FastAPI()
modelo = joblib.load("Modelo_atension.pkl")

# 🎯 Entrada para predicción
class EntradaPrediccion(BaseModel):
    sexo: int
    edad: int
    peso: float
    altura: float
    frutas: int
    vegetales: int
    sal: int
    alcohol: int
    tabaco: int
    vapeo: int
    estres_dias: int
    actividad: int
    colesterol: int
    diabetes: int

# 🎯 Entrada para guardar datos + quiz
class EntradaCompleta(EntradaPrediccion):
    diagnosticado_hta: Union[int, bool]  # ✅ Acepta 0, 1, true, false
    puntaje: int
    respuestas: dict

# 🔁 Funciones auxiliares
def interpretar(prob):
    if prob >= 0.65:
        return "Alto"
    elif prob >= 0.35:
        return "Moderado"
    else:
        return "Bajo"

def codificar_edad(edad_real):
    if 18 <= edad_real <= 24: return 1
    elif edad_real <= 29: return 2
    elif edad_real <= 34: return 3
    elif edad_real <= 39: return 4
    elif edad_real <= 44: return 5
    elif edad_real <= 49: return 6
    elif edad_real <= 54: return 7
    elif edad_real <= 59: return 8
    elif edad_real <= 64: return 9
    elif edad_real <= 69: return 10
    elif edad_real <= 74: return 11
    elif edad_real <= 79: return 12
    elif edad_real <= 100: return 13
    else: return 0

def texto_sexo(s): return "Hombre" if s == 1 else "Mujer"
def texto_binario(v): return "Sí" if v == 1 else "No"
def texto_bool(v): return "Sí" if bool(v) else "No"
def texto_tabaco(v):
    return {
        1: "Fumador diario", 2: "Fumador ocasional", 3: "Exfumador", 4: "No fumador"
    }.get(v, "Desconocido")

def texto_vapeo(v):
    return {
        1: "Todos los días", 2: "Algunos días", 3: "Raramente", 4: "Nunca he usado"
    }.get(v, "Desconocido")

def texto_diabetes(v):
    return {
        0: "No tengo diagnóstico", 1: "Tengo diagnóstico", 2: "No sé"
    }.get(v, "Desconocido")

# 🎯 Endpoint 1: Solo predicción
@app.post("/predict")
def predecir_riesgo(data: EntradaPrediccion):
    try:
        edad_codificada = codificar_edad(data.edad)
        bmi = round(data.peso / ((data.altura / 100) ** 2), 2)

        columnas_ordenadas = [
            edad_codificada, data.sexo, bmi, data.estres_dias,
            data.frutas, data.vegetales, data.sal, data.actividad,
            data.tabaco, data.vapeo, data.alcohol, data.diabetes, data.colesterol
        ]

        prob = modelo.predict_proba([columnas_ordenadas])[0][1]
        nivel = interpretar(prob)

        return {
            "riesgo": nivel,
            "probabilidad": round(prob * 100, 2)
        }

    except Exception as e:
        print(f"💥 Error en guardar_valoracion: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# 🎯 Endpoint 2: Guardar valoración completa
@app.post("/guardar")
def guardar_valoracion(data: EntradaCompleta):
    try:
        edad_codificada = codificar_edad(data.edad)
        bmi = round(data.peso / ((data.altura / 100) ** 2), 2)

        columnas_ordenadas = [
            edad_codificada, data.sexo, bmi, data.estres_dias,
            data.frutas, data.vegetales, data.sal, data.actividad,
            data.tabaco, data.vapeo, data.alcohol, data.diabetes, data.colesterol
        ]

        prob = modelo.predict_proba([columnas_ordenadas])[0][1]
        nivel = interpretar(prob)
        probabilidad = float(round(prob * 100, 2))

        db = SessionLocal()
        nuevo = HTARegistro(
            diagnosticado_hta=texto_binario(data.diagnosticado_hta),
            sexo=texto_sexo(data.sexo),
            edad=data.edad,
            peso=data.peso,
            altura=data.altura,
            bmi=bmi,
            frutas=texto_binario(data.frutas),
            vegetales=texto_binario(data.vegetales),
            sal=texto_binario(data.sal),
            alcohol=texto_binario(data.alcohol),
            actividad=texto_binario(data.actividad),
            tabaco=texto_tabaco(data.tabaco),
            vapeo=texto_vapeo(data.vapeo),
            colesterol=texto_binario(data.colesterol),
            diabetes=texto_diabetes(data.diabetes),
            estres_dias=data.estres_dias,  # ✅ Corregido: asigna directamente el valor numérico
            riesgo=nivel,
            probabilidad=probabilidad,
            puntaje_conocimiento_hta=data.puntaje,
            respuestas_hta=str(data.respuestas)
        )

        db.add(nuevo)
        db.commit()
        db.close()

        return {
            "mensaje": "✅ Datos guardados correctamente",
            "riesgo": nivel,
            "probabilidad": probabilidad
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
