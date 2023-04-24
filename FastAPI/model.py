import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

# Load the data from a CSV file
data = pd.read_csv('merged_data.csv')

# Convert the date column to Unix timestamps
data['date'] = pd.to_datetime(data['date']).astype(int) // 10**9

# Define the input features and the target variable
X = data.drop(['next_week_return', 'symbol'], axis=1)
y = data['next_week_return']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a random forest regression model
model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model on the testing set
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print('Mean squared error:', mse)

# Save the model to a file
joblib.dump(model, 'model.joblib')
