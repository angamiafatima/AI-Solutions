import pandas as pd

# Load the log data
df = pd.read_csv("web_server_logs.csv")

# Display first few rows to inspect
print("Raw Data Preview:")
print(df.head())

# Convert Timestamp column to datetime format
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

# Handle missing or incorrect data
df = df.dropna()  # Remove rows with missing values

# Remove duplicates
df = df.drop_duplicates()

# Convert Response_Code to integer type
df["Response_Code"] = df["Response_Code"].astype(int)

# Save cleaned data to a new CSV file
df.to_csv("cleaned_web_server_logs.csv", index=False)
print("Data processing complete. Cleaned log file saved as 'cleaned_web_server_logs.csv'.")
