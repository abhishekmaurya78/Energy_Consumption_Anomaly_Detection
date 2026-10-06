# app.py - FastAPI Backend for Vercel
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import zipfile

app = FastAPI()

# Static files aur templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dataset load karo zip se
print("Loading dataset...")
with zipfile.ZipFile("household_power_consumption.zip") as z:
    with z.open("household_power_consumption.txt") as f:
        df = pd.read_csv(f, sep=";", na_values="?")

# Data clean karo
df = df[['Date', 'Time', 'Global_active_power']].dropna()
df['Global_active_power'] = pd.to_numeric(df['Global_active_power'], errors='coerce')
df = df.dropna()
df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['Datetime']).set_index('Datetime')

# Hourly average
hourly = df['Global_active_power'].resample('h').mean().dropna()
print(f"Hourly readings: {len(hourly)}")

# Model train karo
X = hourly.values.reshape(-1, 1)
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)
preds = model.predict(X)

# Results store karo
result = pd.DataFrame({
    'Energy_Consumption': hourly.values,
    'Prediction': preds
}, index=hourly.index)
result['Status'] = result['Prediction'].apply(lambda x: 'Normal' if x == 1 else 'Anomaly')

total = len(result)
normal_count = int((result['Status'] == 'Normal').sum())
anomaly_count = int((result['Status'] == 'Anomaly').sum())

print(f"Model ready! Total: {total}, Anomalies: {anomaly_count}")

# ROUTES

# Home page
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# Stats API
@app.get("/api/stats")
async def stats():
    return {
        'total': total,
        'normal': normal_count,
        'anomalies': anomaly_count,
        'anomaly_pct': round(anomaly_count / total * 100, 2),
        'average': round(float(result['Energy_Consumption'].mean()), 3),
        'maximum': round(float(result['Energy_Consumption'].max()), 3),
        'minimum': round(float(result['Energy_Consumption'].min()), 3)
    }

# Time series data
@app.get("/api/timeseries")
async def timeseries():
    sampled = result.iloc[::4]
    data = [{
        'time': idx.strftime('%Y-%m-%d %H:%M'),
        'value': round(float(row['Energy_Consumption']), 3),
        'status': row['Status']
    } for idx, row in sampled.iterrows()]
    return data

# Hourly pattern
@app.get("/api/hourly-pattern")
async def hourly_pattern():
    temp = result.copy()
    temp['Hour'] = temp.index.hour
    pattern = temp.groupby('Hour')['Energy_Consumption'].mean()
    return [{'hour': int(h), 'value': round(float(v), 3)} for h, v in pattern.items()]

# Distribution data
@app.get("/api/distribution")
async def distribution():
    normal_vals = result[result['Status'] == 'Normal']['Energy_Consumption'].tolist()
    anomaly_vals = result[result['Status'] == 'Anomaly']['Energy_Consumption'].tolist()
    return {
        'normal': [round(float(v), 3) for v in normal_vals[::5]],
        'anomaly': [round(float(v), 3) for v in anomaly_vals]
    }

# QA Chatbot
class Question(BaseModel):
    question: str

@app.post("/api/ask")
async def ask(q: Question):
    question = q.question.lower().strip()
    
    if 'total' in question:
        answer = f"Total readings: {total}"
    elif 'average' in question:
        answer = f"Average consumption: {result['Energy_Consumption'].mean():.3f} kW"
    elif 'anomal' in question:
        answer = f"Detected anomalies: {anomaly_count} ({anomaly_count/total*100:.2f}%)"
    elif 'maximum' in question:
        answer = f"Maximum consumption: {result['Energy_Consumption'].max():.3f} kW"
    elif 'minimum' in question:
        answer = f"Minimum consumption: {result['Energy_Consumption'].min():.3f} kW"
    else:
        answer = "Try: total, average, anomalies, maximum, minimum"
    
    return {'answer': answer}