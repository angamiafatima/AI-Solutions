from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session, send_file
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from generate_data import start_log_generation
start_log_generation()

import os


app = Flask(__name__)
app.secret_key = 'secret_key'

USER_CREDENTIALS = {
    'admin': 'password123'
}

data_file = "web_sales_logs.csv"

colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#1abc9c', '#e67e22', '#34495e']


def load_data():
    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)
        if 'cost' not in df.columns:
            df['cost'] = 0
        else:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return pd.DataFrame()

def plot_to_image(fig):
    img_io = io.BytesIO()
    fig.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close(fig) 
    return base64.b64encode(img_io.getvalue()).decode('utf-8')

def apply_filters(df):
    country = request.args.get('country')
    product = request.args.get('product')
    df_filtered = df.copy()

    if country and country != 'All':
        df_filtered = df_filtered[df_filtered['country'] == country]
    if product and product != 'All':
        df_filtered = df_filtered[df_filtered['product'] == product]

    if df_filtered.empty:
        print(f"No data found with filters: country={country}, product={product}")
    return df_filtered

@app.route('/api/filters')
def get_filters():
    df = load_data()
    return jsonify({
        "countries": sorted(df['country'].dropna().unique().tolist()),
        "products": sorted(df['product'].dropna().unique().tolist())
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USER_CREDENTIALS.get(username) == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials, please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    df = load_data()
    df_filtered = apply_filters(df)
    completed_sales = df_filtered[df_filtered['sales_status'] == 'Complete']

    product_revenue = completed_sales.groupby('product')['revenue'].sum()
    country_revenue = completed_sales.groupby('country')['revenue'].sum()

    def safe_float(value):
        return round(float(value), 2) if pd.notna(value) else 0.0

    product_revenue_stats = {
        "min": safe_float(product_revenue.min()) if not product_revenue.empty else 0.0,
        "max": safe_float(product_revenue.max()) if not product_revenue.empty else 0.0,
        "mean": safe_float(product_revenue.mean()) if not product_revenue.empty else 0.0,
        "std": safe_float(product_revenue.std()) if len(product_revenue) > 1 else 0.0,
    }

    country_revenue_stats = {
        "min": safe_float(country_revenue.min()) if not country_revenue.empty else 0.0,
        "max": safe_float(country_revenue.max()) if not country_revenue.empty else 0.0,
        "mean": safe_float(country_revenue.mean()) if not country_revenue.empty else 0.0,
        "std": safe_float(country_revenue.std()) if len(country_revenue) > 1 else 0.0,
    }

    stats = {
        "product_revenue_stats": product_revenue_stats,
        "country_revenue_stats": country_revenue_stats,
    }
    return jsonify(stats)

@app.route('/api/extended_stats')
def extended_stats():
    df = load_data()
    df_filtered = apply_filters(df)
    if df_filtered.empty:
        return jsonify({
            "total_revenue": 0.00,
            "total_profit": 0.00,
            "num_complete_sales": 0,
            "unique_products": 0,
            "total_interactions": 0
        }), 200

    completed_sales = df_filtered[df_filtered['sales_status'] == 'Complete']
    total_revenue = float(completed_sales['revenue'].sum())
    total_cost = float(completed_sales['cost'].sum())
    total_profit = round(total_revenue - total_cost, 2)
    unique_products = int(df_filtered['product'].nunique())
    num_complete_sales = int(completed_sales.shape[0])
    total_interactions = int(df_filtered.shape[0])

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_profit": total_profit,
        "num_complete_sales": num_complete_sales,
        "unique_products": unique_products,
        "total_interactions": total_interactions
    })

# --- PLOTS ---
def generate_plot(data, kind='bar', title='', xlabel='', ylabel=''):
    fig, ax = plt.subplots(figsize=(10, 6)) 
    ax.set_title(title, fontsize=16) 
    if data.empty:
        ax.text(0.5, 0.5, 'No data to display', 
                horizontalalignment='center', verticalalignment='center', 
                transform=ax.transAxes, fontsize=12)
        ax.set_xlabel(xlabel if xlabel else "", fontsize=12) 
        ax.set_ylabel(ylabel if ylabel else "", fontsize=12) 
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        plot_index = data.index
        if not pd.api.types.is_numeric_dtype(plot_index) and not pd.api.types.is_datetime64_any_dtype(plot_index):
            plot_index = data.index.astype(str)

        if kind == 'bar':
            color_cycle = [colors[i % len(colors)] for i in range(len(data))]
            ax.bar(plot_index, data.values, color=color_cycle)
            if plot_index.dtype == 'object' or len(plot_index) > 7: 
                ax.tick_params(axis='x', labelrotation=45, labelsize=10)
            else:
                ax.tick_params(axis='x', labelsize=10)

        elif kind == 'pie':
            pie_labels = data.index.astype(str)
            ax.pie(data.values, labels=pie_labels, autopct='%1.1f%%', 
                   startangle=90, colors=colors[:len(data)], 
                   wedgeprops={'edgecolor': 'white'}, textprops={'fontsize': 10})
            ax.axis('equal') 
        
        elif kind == 'line':
            ax.plot(plot_index, data.values, marker='o', linestyle='-', color=colors[0])
            if pd.api.types.is_datetime64_any_dtype(plot_index) or \
               plot_index.dtype == 'object' or \
               len(plot_index) > 10: 
                ax.tick_params(axis='x', labelrotation=45, labelsize=10)
            else:
                ax.tick_params(axis='x', labelsize=10)
        
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis='y', labelsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7) 

    fig.tight_layout() 
    return plot_to_image(fig)


@app.route('/plot/monthly_revenue')
def plot_monthly_revenue():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        df_completed = df_filtered[df_filtered['sales_status'] == 'Complete'].copy() 
        df_completed['timestamp'] = pd.to_datetime(df_completed['timestamp']) 
        monthly_revenue = df_completed.groupby(pd.Grouper(key='timestamp', freq='M'))['revenue'].sum()
        monthly_revenue.index = monthly_revenue.index.strftime('%Y-%m') 

        return jsonify({"image": generate_plot(monthly_revenue, kind='line', xlabel='Month', ylabel='Total Revenue (£)')})
    except Exception as e:
        print(f"Error in plot_monthly_revenue: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/daily_revenue_trend')
def plot_daily_revenue_trend():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], errors='coerce')
        df_filtered = df_filtered.dropna(subset=['timestamp'])
        df_completed = df_filtered[df_filtered['sales_status'] == 'Complete'].copy()

        if df_completed.empty:
            return jsonify({
                "image": generate_plot(
                    pd.Series(dtype='float64'), 
                    kind='line',
                    xlabel='Date',
                    ylabel='Total Revenue (£)'
                )
            })

        end_date = df_completed['timestamp'].max().normalize()
        start_date = end_date - timedelta(days=6)
        mask = (df_completed['timestamp'] >= start_date) & (df_completed['timestamp'] <= end_date + timedelta(days=1) - timedelta(seconds=1)) 
        df_last_week = df_completed.loc[mask].copy()
        
        df_last_week['date'] = df_last_week['timestamp'].dt.date
        daily_revenue = df_last_week.groupby('date')['revenue'].sum()
        
        all_days_range = pd.date_range(start=start_date, end=end_date, freq='D').date
        daily_revenue = daily_revenue.reindex(all_days_range, fill_value=0)
        daily_revenue.index = pd.to_datetime(daily_revenue.index) 

        return jsonify({
            "image": generate_plot(
                daily_revenue,
                kind='line',
                xlabel='Date',
                ylabel='Total Revenue (£)'
            )
        })
    except Exception as e:
        print(f"Error in plot_daily_revenue_trend: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/plot/hourly_activity')
def plot_hourly_activity():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        df_completed = df_filtered[df_filtered['sales_status'] == 'Complete'].copy()
        df_completed['timestamp'] = pd.to_datetime(df_completed['timestamp'])
        df_completed['hour'] = df_completed['timestamp'].dt.hour
        hourly_revenue = df_completed.groupby('hour')['revenue'].sum()
        hourly_revenue = hourly_revenue.reindex(range(24), fill_value=0).sort_index()


        return jsonify({
            "image": generate_plot(
                hourly_revenue,
                kind='line',
                xlabel='Hour of Day (0-23)',
                ylabel='Total Revenue (£)'
            )
        })
    except Exception as e:
        print(f"Error in plot_hourly_activity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/product_demand')
def plot_product_demand():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        product_demand = df_filtered['product'].value_counts().nlargest(10) 
        return jsonify({"image": generate_plot(product_demand, kind='bar', xlabel='Product', ylabel='Number of Requests')})
    except Exception as e:
        print(f"Error in plot_product_demand: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/sales_status_distribution')
def plot_sales_status_distribution():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        sales_status_data = df_filtered['sales_status'].value_counts()
        sales_status_data = sales_status_data[~sales_status_data.index.isin(['Browse/Event'])]
        return jsonify({"image": generate_plot(sales_status_data, kind='bar', xlabel='Sales Status', ylabel='Count')})
    except Exception as e:
        print(f"Error in plot_sales_status_distribution: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/product_revenue')
def plot_product_revenue():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        completed_sales = df_filtered[df_filtered['sales_status'] == 'Complete']
        product_revenue = completed_sales.groupby('product')['revenue'].sum().nlargest(10).sort_values(ascending=False)
        return jsonify({"image": generate_plot(product_revenue, kind='bar', xlabel='Product', ylabel='Total Revenue (£)')})
    except Exception as e:
        print(f"Error in plot_product_revenue: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/product_conversion_rate')
def plot_product_conversion_rate():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        product_interactions = df_filtered.groupby('product').size()
        completed_sales_by_product = df_filtered[df_filtered['sales_status'] == 'Complete'].groupby('product').size()
        conversion_rate = (completed_sales_by_product.reindex(product_interactions.index, fill_value=0) / product_interactions * 100).fillna(0).nlargest(10).sort_values(ascending=False)
        
        return jsonify({"image": generate_plot(conversion_rate, kind='bar', xlabel='Product', ylabel='Conversion Rate (%)')})
    except Exception as e:
        print(f"Error in plot_product_conversion_rate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/plot/country_distribution')
def plot_country_distribution():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        country_data = df_filtered['country'].value_counts().nlargest(5)
        return jsonify({
            "image": generate_plot(country_data, kind='bar', xlabel='Country', ylabel='Number of Interactions') 
        })
    except Exception as e:
        print(f"Error in plot_country_distribution: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/plot/job_type_distribution')
def plot_job_type_distribution():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        job_type_data = df_filtered['job_type'].value_counts().nlargest(7) 
        return jsonify({
            "image": generate_plot(job_type_data, kind='pie') 
        })
    except Exception as e:
        print(f"Error in plot_job_type_distribution: {e}")
        return jsonify({"error": str(e)}), 500

# Export CSV
@app.route('/export/csv')
def export_csv():
    try:
        df = load_data()
        df_filtered = apply_filters(df)
        csv_buffer = StringIO()
        df_filtered.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        byte_buffer = BytesIO(csv_buffer.getvalue().encode('utf-8'))
        
        filename = f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(byte_buffer, mimetype='text/csv', as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return jsonify({"error": str(e)}), 500

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port)