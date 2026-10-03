import joblib

m = joblib.load("model.pkl")
print("Model type :", type(m).__name__)
print("n_features :", getattr(m, "n_features_in_", "?"))
print("Features   :")
for i, f in enumerate(getattr(m, "feature_names_in_", []), 1):
    print(f"  {i:2d}. {f}")