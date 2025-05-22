# AI Solutions Dashboard

This project is a web-based dashboard for analyzing and visualizing web sales log data using Python. It helps businesses gain insights from raw logs in a user-friendly interface.

## 🚀 Features

- Upload and process web sales log data
- Visualize analytics in real-time
- Detect anomalies and trends
- Interactive charts and tables

## 🛠️ Tech Stack

- Python
- Flask (Web Framework)
- Pandas, Matplotlib (Data Analysis and Visualization)
- HTML/CSS (Frontend Templates)
- Hosted on Render, version control via GitHub

## 🧾 File Structure

├── app.py # Main Flask app
├── generate_data.py # Simulated data generator
├── process_logs.py # Data processing script
├── analyse_logs.py # Log analysis script
├── templates/ # HTML templates for the frontend
├── requirements.txt # Python dependencies
├── Procfile # For Render deployment
└── web_sales_logs.csv # Sample dataset


## 📦 Installation

```bash
git clone https://github.com/angamiafatima/AI-Solutions.git
cd AI-Solutions
pip install -r requirements.txt
python app.py

Visit the app at http://localhost:5000 in your browser.

Deployment
This app is deployed on Render. It uses a Procfile and automatic GitHub deployment.

License
MIT License

Author
Fatima Angamia
