# app.py - Flask Backend
# Energy Consumption Anomaly Detection

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import zipfile
from sklearn.ensemble import IsolationForest

app = Flask(__name__)

# LOAD DATA & TRAIN MODEL ONCE (startup process)
print("=" * 50)
print("Energy Anomaly Detection - Starting Server")
print("=" * 50)

print("\n[1/4] Loading dataset...")
with zipfile.ZipFile("household_power_consumption.zip") as z:
    with z.open("household_power_consumption.txt") as f:
        df = pd.read_csv(f, sep=";", na_values="?")

df = df[['Date', 'Time', 'Global_active_power']].dropna()
print(f"      Loaded {len(df):,} rows")

print("\n[2/4] Cleaning data...")
df['Global_active_power'] = pd.to_numeric(df['Global_active_power'], errors='coerce')
df = df.dropna()
df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'],
                                 dayfirst=True, errors='coerce')
df = df.dropna(subset=['Datetime']).set_index('Datetime')

print("\n[3/4] Resampling to hourly...")
hourly = df['Global_active_power'].resample('h').mean().dropna()
print(f"      Hourly readings: {len(hourly):,}")

print("\n[4/4] Training Isolation Forest model...")
X = hourly.values.reshape(-1, 1)
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)
preds = model.predict(X)

result = pd.DataFrame({
    'Energy_Consumption': hourly.values,
    'Prediction': preds
}, index=hourly.index)
result['Status'] = result['Prediction'].apply(
    lambda x: 'Normal' if x == 1 else 'Anomaly'
)

total = len(result)
normal_count = int((result['Status'] == 'Normal').sum())
anomaly_count = int((result['Status'] == 'Anomaly').sum())

print(f"\n✓ Model ready!")
print(f"  Total: {total:,}")
print(f"  Normal: {normal_count:,}")
print(f"  Anomalies: {anomaly_count:,} ({anomaly_count/total*100:.2f}%)")
print("\n" + "=" * 50)
print("Server starting at: http://localhost:5000")
print("=" * 50 + "\n")


# ROUTES

@app.route('/')
def home():
    """Main page"""
    return render_template('index.html')


@app.route('/api/stats')
def stats():
    """Overall statistics"""
    return jsonify({
        'total': total,
        'normal': normal_count,
        'anomalies': anomaly_count,
        'anomaly_pct': round(anomaly_count / total * 100, 2),
        'average': round(float(result['Energy_Consumption'].mean()), 3),
        'maximum': round(float(result['Energy_Consumption'].max()), 3),
        'minimum': round(float(result['Energy_Consumption'].min()), 3)
    })


@app.route('/api/timeseries')
def timeseries():
    """Time series data (sampled for performance)"""
    sampled = result.iloc[::4]
    data = [{
        'time': idx.strftime('%Y-%m-%d %H:%M'),
        'value': round(float(row['Energy_Consumption']), 3),
        'status': row['Status']
    } for idx, row in sampled.iterrows()]
    return jsonify(data)


@app.route('/api/hourly-pattern')
def hourly_pattern():
    """Average consumption by hour of day"""
    temp = result.copy()
    temp['Hour'] = temp.index.hour
    pattern = temp.groupby('Hour')['Energy_Consumption'].mean()
    return jsonify([{
        'hour': int(h),
        'value': round(float(v), 3)
    } for h, v in pattern.items()])


@app.route('/api/distribution')
def distribution():
    """Distribution data for histogram"""
    normal_vals = result[result['Status'] == 'Normal']['Energy_Consumption'].tolist()
    anomaly_vals = result[result['Status'] == 'Anomaly']['Energy_Consumption'].tolist()

    normal_sampled = [round(float(v), 3) for v in normal_vals[::5]]
    anomaly_sampled = [round(float(v), 3) for v in anomaly_vals]

    return jsonify({
        'normal': normal_sampled,
        'anomaly': anomaly_sampled
    })


@app.route('/api/ask', methods=['POST'])
def ask():
    """QA system"""
    data = request.get_json()
    q = data.get('question', '').lower().strip()

    if not q:
        answer = "Please ask a question. Type 'help' for options."

    elif 'help' in q:
        answer = ("Available questions:\n"
                  "• total — Total readings\n"
                  "• average — Average consumption\n"
                  "• maximum — Highest consumption\n"
                  "• minimum — Lowest consumption\n"
                  "• anomalies — Detected anomalies\n"
                  "• status — Overall status\n"
                  "• show anomalies — List top anomalies")

    elif 'total' in q or 'how many' in q:
        answer = f"Total readings: {total:,}"

    elif 'normal' in q and 'show' not in q:
        answer = f"Normal readings: {normal_count:,}"

    elif 'anomal' in q or 'abnormal' in q:
        if 'show' in q or 'list' in q:
            top = result[result['Status'] == 'Anomaly'].head(5)
            lines = ["Top 5 anomalies:"]
            for idx, row in top.iterrows():
                lines.append(f"  • {idx.strftime('%Y-%m-%d %H:%M')} → {row['Energy_Consumption']:.3f} kW")
            answer = "\n".join(lines)
        elif 'percent' in q or 'percentage' in q:
            answer = f"Anomaly percentage: {anomaly_count/total*100:.2f}%"
        else:
            answer = f"Detected anomalies: {anomaly_count:,} ({anomaly_count/total*100:.2f}%)"

    elif 'average' in q or 'mean' in q:
        avg = result['Energy_Consumption'].mean()
        answer = f"Average consumption: {avg:.3f} kW"

    elif 'maximum' in q or 'highest' in q or 'max' in q:
        mx = result['Energy_Consumption'].max()
        peak_time = result['Energy_Consumption'].idxmax()
        answer = f"Maximum consumption: {mx:.3f} kW\nPeak at: {peak_time.strftime('%Y-%m-%d %H:%M')}"

    elif 'minimum' in q or 'lowest' in q or 'min' in q:
        mn = result['Energy_Consumption'].min()
        low_time = result['Energy_Consumption'].idxmin()
        answer = f"Minimum consumption: {mn:.3f} kW\nLowest at: {low_time.strftime('%Y-%m-%d %H:%M')}"

    elif 'status' in q or 'condition' in q:
        answer = (f"Status:\n"
                  f"  • Total: {total:,}\n"
                  f"  • Normal: {normal_count:,}\n"
                  f"  • Anomalies: {anomaly_count:,} ({anomaly_count/total*100:.2f}%)")

    elif 'show normal' in q:
        answer = f"Normal readings: {normal_count:,} (first 5 shown in CSV)"

    else:
        answer = "Sorry, I don't understand. Type 'help' for available options."

    return jsonify({'answer': answer})


# RUN

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)