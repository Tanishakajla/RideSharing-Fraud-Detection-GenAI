import joblib
import pandas as pd

model = joblib.load('fraud_model.joblib')

cols = ['fare','seconds_since_signup','user_trip_count','user_trips_last_1h','num_users_on_device','device_degree','card_degree']

tests = [
    [10, 1000, 0, 0, 1, 1, 1],
    [200, 100, 50, 3, 4, 10, 20],
    [50, 1000000, 100, 10, 5, 2, 2],
    [5, 10, 0, 0, 0, 1, 1]
]

for t in tests:
    df = pd.DataFrame([t], columns=cols)
    try:
        proba = model.predict_proba(df)[0][1]
    except Exception as e:
        print('ERROR for input', t, e)
        continue
    print('input:', t, '=> fraud_prob:', proba)
