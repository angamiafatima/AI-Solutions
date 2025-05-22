import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the cleaned log data
df = pd.read_csv("cleaned_web_server_logs.csv")

# Display basic statistics
print("Basic Statistics:")
print(df.describe())

# Count requests per type
request_counts = df["Request_Type"].value_counts()

# Plot request type distribution
plt.figure(figsize=(8,5))
sns.barplot(x=request_counts.index, y=request_counts.values, palette="Blues")
plt.xlabel("Request Type")
plt.ylabel("Count")
plt.title("Distribution of Request Types")
plt.show()

# Count occurrences of different URLs
url_counts = df["URL"].value_counts().head(10)  # Top 10 most requested URLs

# Plot top requested URLs
plt.figure(figsize=(10,5))
sns.barplot(x=url_counts.index, y=url_counts.values, palette="Greens")
plt.xlabel("URL")
plt.ylabel("Count")
plt.title("Top Requested URLs")
plt.xticks(rotation=45)
plt.show()

# Analyze response codes
response_counts = df["Response_Code"].value_counts()

# Plot response code distribution
plt.figure(figsize=(8,5))
sns.barplot(x=response_counts.index, y=response_counts.values, palette="Reds")
plt.xlabel("Response Code")
plt.ylabel("Count")
plt.title("Response Code Distribution")
plt.show()
