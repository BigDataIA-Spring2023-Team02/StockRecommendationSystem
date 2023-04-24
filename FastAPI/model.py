import os
import boto3
import joblib
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

load_dotenv()
# Authenticate S3 client for logging with your user credentials that are stored in your .env config file
s3Client = boto3.client('s3',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

merged_data = s3Client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/doshimee11_merged_data.csv')['Body'].read().decode('utf-8')
data = pd.read_csv(StringIO(merged_data))
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

# Save the model to a file
joblib.dump(model, 'model.joblib')
with open('model.joblib', "rb") as f:
    s3Client.upload_fileobj(f, os.environ.get('USER_BUCKET_NAME'), 'model.joblib')
