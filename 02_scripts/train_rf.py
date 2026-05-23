import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base, "01_datos_procesados", "sismos_procesados.parquet")
    model_dir = os.path.join(base, "04_modelos")
    model_path = os.path.join(model_dir, "random_forest_regressor.joblib")
    
    print(f"Loading data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    # Predictors: lat, lon, depth
    # Target: magnitude
    X = df[['lat', 'lon', 'depth']]
    y = df['magnitude']
    
    print(f"Training Random Forest Regressor on {len(df)} samples...")
    # Best params from GridSearchCV or simple robust parameters
    # Let's train a good model
    rf = RandomForestRegressor(n_estimators=100, max_depth=20, min_samples_split=5, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    os.makedirs(model_dir, exist_ok=True)
    print(f"Saving model to {model_path}...")
    joblib.dump(rf, model_path)
    print("Model trained and saved successfully!")

if __name__ == "__main__":
    main()
