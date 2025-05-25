import os
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# 🎯 Modelo ML
model = joblib.load("Modelo1.pkl")

# 🎯 Base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 🎯 Tabla
class HTARegistro(Base):
    __tablename__ = "evaluacion_hta"
    id = Column(Integer, primary_key=True, index=True)
    genero = Column(String(10), nullable=False)
    edad = Column(Integer, nullable=False)
    bmi = Column(Numeric(5, 2), nullable=False)
    actividad_fisica = Column(String(20), nullable=False)
    horas_sueno = Column(Numeric(4, 2), nullable=False)
    frecuencia_fumar = Column(String(20), nullable=False)
    antecedentes_familiares = Column(String(20), nullable=False)
    nivel_estres = Column(Integer, nullable=False)
    nivel_consumo_alcohol = Column(String(20))
    nivel_consumo_sal = Column(String(20))
    hta_diagnosticada_previamente = Column(String(5))
    puntaje_conocimiento_hta = Column(Integer)
    respuestas_hta = Column(String)  # JSON simplificado como string
    riesgo = Column(String(10), nullable=False)
    probabilidad = Column(Numeric(5, 2), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

# ✅ Crear tabla si no existe
Base.metadata.create_all(bind=engine)

# 🎯 FastAPI
app = FastAPI()

class InputData(BaseModel):
    Gender: str
    Age: float
    BMI: float
    Physical_Activity_Level: str
    Sleep_Duration: float
    Smoking_Status: str
    Family_History: str
    Stress_Level: int
    Alcohol_Level: str
    Salt_Level: str
    Previously_Diagnosed: str
    HTA_Quiz_Score: int
    HTA_Quiz_Answers: dict

@app.post("/predict")
def predict(data: InputData):
    try:
        df = pd.DataFrame([{
            "Gender": data.Gender,
            "Age": data.Age,
            "BMI": data.BMI,
            "Physical_Activity_Level": data.Physical_Activity_Level,
            "Sleep_Duration": data.Sleep_Duration,
            "Smoking_Status": data.Smoking_Status,
            "Family_History": 1 if data.Family_History.lower() == "yes" else 0,
            "Stress_Level": data.Stress_Level,
            "Alcohol_Level": data.Alcohol_Level,
            "Salt_Level": data.Salt_Level
        }])
        prob = model.predict_proba(df)[0][1]
        if prob >= 0.75:
            riesgo = "Alto"
        elif prob >= 0.5:
            riesgo = "Moderado"
        else:
            riesgo = "Bajo"

        db = SessionLocal()
        nuevo = HTARegistro(
            genero=data.Gender,
            edad=int(data.Age),
            bmi=round(data.BMI, 2),
            actividad_fisica=data.Physical_Activity_Level,
            horas_sueno=round(data.Sleep_Duration, 2),
            frecuencia_fumar=data.Smoking_Status,
            antecedentes_familiares=data.Family_History,
            nivel_estres=data.Stress_Level,
            nivel_consumo_alcohol=data.Alcohol_Level,
            nivel_consumo_sal=data.Salt_Level,
            hta_diagnosticada_previamente=data.Previously_Diagnosed,
            puntaje_conocimiento_hta=data.HTA_Quiz_Score,
            respuestas_hta=str(data.HTA_Quiz_Answers),
            riesgo=riesgo,
            probabilidad=round(prob, 2)
        )
        db.add(nuevo)
        db.commit()
        db.close()

        return {"riesgo": riesgo, "probabilidad": round(prob, 2)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🧪 Dummy interfaz Gradio obligatoria
def dummy(): return "API activa"
gr.Interface(fn=dummy, inputs=[], outputs="text").launch()
