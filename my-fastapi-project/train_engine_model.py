# -*- coding: utf-8 -*-
"""
train_engine_model.py
เทรนโมเดลประเมินความเสี่ยงเครื่องยนต์ผิดปกติ (%) สำหรับ AIEngineHealth
ชุดข้อมูล: Automotive Vehicles Engine Health Dataset (Kaggle) -> engine_data.csv

วิธีรัน (บนเซิร์ฟเวอร์ ใน venv เดียวกับ main.py):
    source venv/bin/activate
    python train_engine_model.py

ผลลัพธ์:
    engine_model.pkl   -> ไฟล์โมเดล (main.py จะโหลดไฟล์นี้)
    model_info.json    -> สรุปผลและค่าต่าง ๆ ให้คนอ่าน
"""
import json
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# ==============================================================================
# ตั้งค่า (แก้ตรงนี้ได้)
# ==============================================================================
DATA_FILE = "engine_data.csv"
OUTPUT_MODEL = "engine_model.pkl"
OUTPUT_INFO = "model_info.json"
RANDOM_STATE = 42

# ⚠️ สำคัญ: label ไหนหมายถึง "ผิดปกติ" ต้องตรวจจากหน้า Kaggle ต้นฉบับก่อน
# ค่าเริ่มต้นตั้งตาม README ที่ระบุว่า 0 = normal, 1 = faulty
FAULTY_LABEL = 1

# เกณฑ์แบ่งสถานะจากความเสี่ยง (%)
RISK_THRESHOLDS = {"warning": 40.0, "danger": 70.0}

# ชื่อคอลัมน์มาตรฐานที่ระบบจะใช้ทั้งหมด (เรียงตามลำดับนี้เสมอ)
FEATURES = [
    "engine_rpm",
    "lub_oil_pressure",
    "fuel_pressure",
    "coolant_pressure",
    "lub_oil_temp",
    "coolant_temp",
]
TARGET = "engine_condition"

# รองรับชื่อคอลัมน์หลายแบบ (Kaggle / Hugging Face ตั้งชื่อไม่เหมือนกัน)
COLUMN_ALIASES = {
    "engine_rpm": "engine_rpm",
    "lub_oil_pressure": "lub_oil_pressure",
    "fuel_pressure": "fuel_pressure",
    "coolant_pressure": "coolant_pressure",
    "lub_oil_temp": "lub_oil_temp",
    "lub_oil_temperature": "lub_oil_temp",
    "coolant_temp": "coolant_temp",
    "coolant_temperature": "coolant_temp",
    "engine_condition": "engine_condition",
}


def normalize(name: str) -> str:
    return "_".join(str(name).strip().lower().replace("-", " ").replace("_", " ").split())


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    renamed = {c: COLUMN_ALIASES.get(normalize(c), normalize(c)) for c in df.columns}
    df = df.rename(columns=renamed)

    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        print(f"❌ ไม่พบคอลัมน์: {missing}")
        print(f"   คอลัมน์ที่มีในไฟล์: {list(df.columns)}")
        sys.exit(1)
    return df[FEATURES + [TARGET]]


def main():
    print(f"scikit-learn {sklearn.__version__} | numpy {np.__version__} | pandas {pd.__version__}\n")

    # ------------------------------------------------------------------
    # 1) โหลดและตรวจข้อมูล
    # ------------------------------------------------------------------
    df = load_data(DATA_FILE)
    print(f"📂 โหลดข้อมูล {len(df):,} แถว")

    n_missing = int(df.isna().sum().sum())
    n_dup = int(df.duplicated().sum())
    print(f"   ค่าว่าง: {n_missing} | แถวซ้ำ: {n_dup}")
    df = df.dropna().drop_duplicates().reset_index(drop=True)

    labels = sorted(df[TARGET].unique().tolist())
    if len(labels) != 2 or FAULTY_LABEL not in labels:
        print(f"❌ label ที่พบ: {labels} (ต้องมี 2 ค่า และมี FAULTY_LABEL={FAULTY_LABEL})")
        sys.exit(1)

    counts = df[TARGET].value_counts().sort_index()
    print("\n📊 สัดส่วนคลาส:")
    for lab, cnt in counts.items():
        tag = "ผิดปกติ" if lab == FAULTY_LABEL else "ปกติ"
        print(f"   {lab} ({tag}): {cnt:,} ({cnt / len(df):.1%})")
    baseline_acc = counts.max() / len(df)
    print(f"   👉 Baseline (ทายคลาสที่เยอะที่สุดตลอด) = {baseline_acc:.1%}  โมเดลต้องดีกว่านี้")

    print("\n🔎 ค่าเฉลี่ยแต่ละคลาส (ใช้เช็กว่า label ผิดปกติถูกฝั่งไหม):")
    print(df.groupby(TARGET)[FEATURES].mean().round(2).T.to_string())

    X = df[FEATURES]
    y = (df[TARGET] == FAULTY_LABEL).astype(int)  # 1 = ผิดปกติ เสมอหลังจากนี้

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    # ------------------------------------------------------------------
    # 2) เปรียบเทียบโมเดลด้วย 5-Fold Cross Validation (ROC-AUC)
    # ------------------------------------------------------------------
    candidates = {
        "LogisticRegression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=10, min_samples_leaf=5,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_depth=6,
            class_weight="balanced", random_state=RANDOM_STATE,
        ),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = {}
    print("\n🤖 เปรียบเทียบโมเดล (5-Fold CV, ROC-AUC):")
    for name, model in candidates.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        cv_scores[name] = float(scores.mean())
        print(f"   {name:<22} AUC = {scores.mean():.3f} ± {scores.std():.3f}")

    best_name = max(cv_scores, key=cv_scores.get)
    best_model = candidates[best_name]
    print(f"   🏆 เลือก: {best_name}")

    # ------------------------------------------------------------------
    # 3) วัดผลบน Test set (ข้อมูลที่โมเดลไม่เคยเห็น)
    # ------------------------------------------------------------------
    best_model.fit(X_train, y_train)
    proba = best_model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "model": best_name,
        "baseline_accuracy": round(float(baseline_acc), 4),
        "cv_roc_auc": {k: round(v, 4) for k, v in cv_scores.items()},
        "test_accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "test_f1_faulty": round(float(f1_score(y_test, pred)), 4),
        "test_roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }

    print("\n📈 ผลบน Test set:")
    print(f"   Accuracy : {metrics['test_accuracy']:.3f}  (baseline {baseline_acc:.3f})")
    print(f"   F1 (ผิดปกติ): {metrics['test_f1_faulty']:.3f}")
    print(f"   ROC-AUC  : {metrics['test_roc_auc']:.3f}")
    print("   Confusion Matrix [[ปกติ→ปกติ, ปกติ→ผิดปกติ], [ผิดปกติ→ปกติ, ผิดปกติ→ผิดปกติ]]:")
    print(f"   {metrics['confusion_matrix']}")
    print(classification_report(y_test, pred, target_names=["ปกติ", "ผิดปกติ"], digits=3))

    # ------------------------------------------------------------------
    # 4) เทรนครั้งสุดท้ายด้วยข้อมูลทั้งหมด แล้วบันทึก
    # ------------------------------------------------------------------
    best_model.fit(X, y)

    feature_stats = {
        f: {
            "min": round(float(X[f].min()), 3),
            "p01": round(float(X[f].quantile(0.01)), 3),
            "median": round(float(X[f].median()), 3),
            "p99": round(float(X[f].quantile(0.99)), 3),
            "max": round(float(X[f].max()), 3),
        }
        for f in FEATURES
    }

    bundle = {
        "model": best_model,               # predict_proba(...)[:, 1] = ความน่าจะเป็นที่ผิดปกติ
        "features": FEATURES,              # ลำดับคอลัมน์ที่ต้องส่งเข้าโมเดล
        "risk_thresholds": RISK_THRESHOLDS,
        "feature_stats": feature_stats,    # ใช้ตรวจค่าที่ผู้ใช้กรอกว่าอยู่ในช่วงที่โมเดลรู้จักไหม
        "metrics": metrics,
        "original_faulty_label": FAULTY_LABEL,
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }
    joblib.dump(bundle, OUTPUT_MODEL, compress=3)

    info = {k: v for k, v in bundle.items() if k != "model"}
    with open(OUTPUT_INFO, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 5) ทดสอบโหลดกลับและทำนาย 1 ตัวอย่าง (ค่ากลางของข้อมูล)
    # ------------------------------------------------------------------
    loaded = joblib.load(OUTPUT_MODEL)
    sample = pd.DataFrame([{f: feature_stats[f]["median"] for f in FEATURES}])[loaded["features"]]
    risk = float(loaded["model"].predict_proba(sample)[0, 1]) * 100
    print(f"\n💾 บันทึก {OUTPUT_MODEL} และ {OUTPUT_INFO} แล้ว")
    print(f"🧪 ทดสอบด้วยค่ากลาง -> ความเสี่ยงผิดปกติ {risk:.1f}%")

    print("\n📏 ช่วงค่าของข้อมูล (ไว้ใช้ทำฟอร์มหน้าเว็บ):")
    for f, s in feature_stats.items():
        print(f"   {f:<18} min={s['min']:<10} median={s['median']:<10} max={s['max']}")


if __name__ == "__main__":
    main()