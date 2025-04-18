from flask import Flask, render_template, request, redirect, url_for
import json
import os
import requests

app = Flask(__name__)

# Пути к JSON-файлам
PATIENTS_FILE = 'patients.json'
PRESCRIPTIONS_FILE = 'prescriptions.json'

# -------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ --------------------
def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# -------------------- НАЧАЛЬНАЯ СТРАНИЦА --------------------
@app.route('/')
def index():
    return render_template('index.html')

# -------------------- ИНТЕРФЕЙС БОЛЬНИЦЫ --------------------
@app.route('/hospital', methods=['GET', 'POST'])
def hospital():
    if request.method == 'POST':
        patient = {
            "id": request.form['id'],
            "name": request.form['name'],
            "medical_history": request.form['medical_history']
        }
        patients = load_data(PATIENTS_FILE)
        patients.append(patient)
        save_data(PATIENTS_FILE, patients)
        return redirect(url_for('hospital'))
    patients = load_data(PATIENTS_FILE)
    return render_template('hospital.html', patients=patients)

# -------------------- ИНТЕРФЕЙС АПТЕКИ --------------------
@app.route('/pharmacy', methods=['GET', 'POST'])
def pharmacy():
    patients = load_data(PATIENTS_FILE)
    if request.method == 'POST':
        prescription = {
            "patient_id": request.form['patient_id'],
            "medication": request.form['medication']
        }
        prescriptions = load_data(PRESCRIPTIONS_FILE)
        prescriptions.append(prescription)
        save_data(PRESCRIPTIONS_FILE, prescriptions)
        return redirect(url_for('pharmacy'))
    return render_template('pharmacy.html', patients=patients)

# -------------------- ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ --------------------
@app.route('/user')
def user():
    patients = load_data(PATIENTS_FILE)
    return render_template('user.html', patients=patients)

@app.route('/chat', methods=['POST'])
def chat():
    patient_id = request.form['patient_id']
    user_message = request.form['message']

    patients = load_data(PATIENTS_FILE)
    prescriptions = load_data(PRESCRIPTIONS_FILE)

    patient = next((p for p in patients if str(p['id']) == patient_id), None)
    patient_prescriptions = [r for r in prescriptions if str(r['patient_id']) == patient_id]

    if not patient:
        return "Пациент не найден", 404

    history_text = f"История болезни: {patient['medical_history']}\n"
    prescription_text = "Назначения: " + ", ".join([p['medication'] for p in patient_prescriptions])

    system_prompt = f"""
Ты — медицинский помощник. У тебя есть данные о пациенте:
{history_text}
{prescription_text}

На основе этого, помоги пользователю — предложи, к какому врачу обратиться, стоит ли срочно идти в больницу, и какие меры предпринять.
"""

    url = "https://gpt-4o.p.rapidapi.com/chat/completions"
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }
    headers = {
        "x-rapidapi-host": "gpt-4o.p.rapidapi.com",
        "x-rapidapi-key": "ТВОЙ_RAPIDAPI_КЛЮЧ",  # <-- вставь свой ключ сюда
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    ai_response = data['choices'][0]['message']['content']

    return render_template("chat.html", message=user_message, response=ai_response, patient=patient)

# -------------------- ЗАПУСК --------------------
if __name__ == '__main__':
    app.run(debug=True)
