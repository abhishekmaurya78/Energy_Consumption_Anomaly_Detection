# ENERGY CONSUMPTION ANOMALY DETECTION
# WITH USER QUESTION ANSWERING

# 1. Import libraries
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

# 2. Load electricity dataset
df = pd.read_csv(
    "household_power_consumption.txt",
    sep=";",
    na_values="?"
)

# 3. Select required columns
df = df[['Date', 'Time', 'Global_active_power']]

# 4. Clean data
df = df.dropna()

# 5. Convert electricity consumption into numeric
df['Global_active_power'] = pd.to_numeric(
    df['Global_active_power'],
    errors='coerce'
)

df = df.dropna()

# 6. Create timestamp
df['Datetime'] = pd.to_datetime(
    df['Date'] + ' ' + df['Time'],
    dayfirst=True,
    errors='coerce'
)

df = df.dropna(subset=['Datetime'])

# 7. Calculate actual hourly average
df = df.set_index('Datetime')

hourly_data = (
    df['Global_active_power']
    .resample('h')
    .mean()
    .dropna()
)

# 8. Prepare data for ML
X = hourly_data.values.reshape(-1, 1)

# 9. Create ML model
model = IsolationForest(
    contamination=0.05,
    random_state=42
)

# 10. Train model
model.fit(X)

# 11. Predict anomalies
predictions = model.predict(X)

# 12. Store results
result = pd.DataFrame({
    'Energy_Consumption': hourly_data.values,
    'Prediction': predictions
}, index=hourly_data.index)

result['Status'] = result['Prediction'].apply(
    lambda x: 'Normal' if x == 1 else 'Anomaly'
)

# 13. Calculate statistics
total = len(result)

normal = len(result[result['Status'] == 'Normal'])

anomalies = len(result[result['Status'] == 'Anomaly'])

average = result['Energy_Consumption'].mean()

maximum = result['Energy_Consumption'].max()

minimum = result['Energy_Consumption'].min()

# 14. User question answering function

def ask_question():

    print("\nENERGY AI ASSISTANT")
    print("Type 'exit' to stop.")

    while True:

        question = input("\nAsk your question: ").lower()

        if question == "exit":
            print("Thank you!")
            break

        elif "total" in question or "how many readings" in question:
            print("Total readings:", total)

        elif "normal" in question:
            print("Normal readings:", normal)

        elif "anomal" in question or "abnormal" in question:
            print("Detected anomalies:", anomalies)

        elif "average" in question or "mean" in question:
            print("Average consumption:", round(average, 3), "kW")

        elif "maximum" in question or "highest" in question:
            print("Maximum consumption:", round(maximum, 3), "kW")

        elif "minimum" in question or "lowest" in question:
            print("Minimum consumption:", round(minimum, 3), "kW")

        elif "show anomalies" in question or "list anomalies" in question:
            print(result[result['Status'] == 'Anomaly'])

        elif "show normal" in question:
            print(result[result['Status'] == 'Normal'])

        elif "status" in question or "condition" in question:
            anomaly_percentage = anomalies / total * 100

            print("Anomaly percentage:", round(anomaly_percentage, 2), "%")

            print("Normal readings:", normal)
            print("Anomalies:", anomalies)

        else:
            print("Sorry, I don't understand that question.")
            print("Try asking about average, maximum, minimum,")
            print("normal readings, anomalies or total readings.")

# 15. Save results to CSV
result.to_csv("results.csv")
print("Results saved to results.csv")

# 15. Start chatbot
ask_question()

# 16. Visualize results
plt.figure(figsize=(12, 5))

plt.plot(
    result.index,
    result['Energy_Consumption'],
    label='Energy Consumption'
)

anomaly_data = result[result['Status'] == 'Anomaly']

plt.scatter(
    anomaly_data.index,
    anomaly_data['Energy_Consumption'],
    color='red',
    label='Anomaly'
)

plt.xlabel("Date and Time")
plt.ylabel("Global Active Power (kW)")
plt.title("Energy Consumption Anomaly Detection")

plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("anomaly_plot.png", dpi=150, bbox_inches='tight')
print("\nGraph saved to anomaly_plot.png")
plt.show()
