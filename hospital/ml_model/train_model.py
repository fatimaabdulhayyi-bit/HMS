import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. Load both the training and testing files
train_df = pd.read_csv("Training.csv")
test_df = pd.read_csv("Testing.csv")

# 2. Prepare the training data
X_train = train_df.drop('Department', axis=1)
y_train = train_df['Department']

# 3. Prepare the testing data
X_test = test_df.drop('Department', axis=1)
y_test = test_df['Department']

# 4. Initialize and train the Random Forest Classifier
print("Training the model, please wait...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate the model using testing data
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Training completed successfully! Final Test Accuracy: {accuracy*100:.2f}%")

MODEL_FILE_PATH = "disease_model.pkl"
FEATURES_FILE_PATH = "symptom_features.pkl"

# Save the trained model object
with open(MODEL_FILE_PATH, "wb") as f:
    pickle.dump(model, f)

# Save the list of symptom columns (Features)
with open(FEATURES_FILE_PATH, "wb") as f:
    pickle.dump(list(X_train.columns), f)

print("Model and features have been successfully saved!")