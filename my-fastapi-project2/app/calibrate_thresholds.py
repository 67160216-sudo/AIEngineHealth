# -*- coding: utf-8 -*-
"""
calibrate_thresholds.py
ตั้งเกณฑ์สถานะ (ปกติ / เฝ้าระวัง / อันตราย) จากข้อมูลจริง แทนการเดาตัวเลขกลม ๆ

หลักการ: ดูว่าเครื่องยนต์ที่ "ปกติจริง" ในข้อมูล ได้คะแนนความเสี่ยงจาก AI เท่าไร
  - เกณฑ์เฝ้าระวัง = เปอร์เซ็นไทล์ที่ 75 ของเครื่องปกติ  (เครื่องปกติ 75% จะไม่ถูกเตือน)
  - เกณฑ์อันตราย  = เปอร์เซ็นไทล์ที่ 95 ของเครื่องปกติ  (เครื่องปกติ 95% จะไม่ถูกจัดว่าอันตราย)
คะแนนที่ใช้มาจาก 5-Fold Cross Validation (โมเดลไม่เคยเห็นแถวนั้นตอนเทรน) จึงไม่ลำเอียง

วิธีรัน (โฟลเดอร์เดียวกับ engine_data.csv, engine_model.pkl, train_engine_model.py):
    source venv/bin/activate
    python calibrate_thresholds.py
ผลลัพธ์: risk_thresholds.json  (engine_ai.py จะอ่านอัตโนมัติหลังรีสตาร์ต API)
"""
import json

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from train_engine_model import DATA_FILE, FAULTY_LABEL, FEATURES, RANDOM_STATE, TARGET, load_data

WARN_PCT = 75
DANGER_PCT = 95

df = load_data(DATA_FILE).dropna().drop_duplicates().reset_index(drop=True)
X = df[FEATURES]
y = (df[TARGET] == FAULTY_LABEL).astype(int).values

bundle = joblib.load("engine_model.pkl")
print(f"⏳ คำนวณคะแนนแบบ 5-Fold ด้วย {bundle['metrics']['model']} (อาจใช้เวลาสักครู่) ...", flush=True)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
risk = cross_val_predict(clone(bundle["model"]), X, y, cv=cv, method="predict_proba")[:, 1] * 100

healthy, faulty = risk[y == 0], risk[y == 1]
print("\n📊 การกระจายคะแนนความเสี่ยง (%)")
print(f"{'':10}{'p25':>8}{'p50':>8}{'p75':>8}{'p90':>8}{'p95':>8}")
for name, arr in [("ปกติ", healthy), ("มีปัญหา", faulty)]:
    print(f"{name:10}" + "".join(f"{np.percentile(arr, q):8.1f}" for q in (25, 50, 75, 90, 95)))

warning = round(float(np.percentile(healthy, WARN_PCT)), 1)
danger = round(float(np.percentile(healthy, DANGER_PCT)), 1)
if danger < warning + 5:
    danger = round(warning + 5, 1)

def share(arr, thr):
    return (arr >= thr).mean() * 100

print(f"\n🎯 เกณฑ์ที่ได้: เฝ้าระวัง ≥ {warning}%  |  อันตราย ≥ {danger}%")
print(f"   เครื่องปกติที่ถูกเตือน (เฝ้าระวังขึ้นไป): {share(healthy, warning):.1f}%")
print(f"   เครื่องปกติที่ถูกจัดว่าอันตราย        : {share(healthy, danger):.1f}%")
print(f"   เครื่องมีปัญหาที่ถูกเตือน            : {share(faulty, warning):.1f}%")
print(f"   เครื่องมีปัญหาที่ถูกจัดว่าอันตราย     : {share(faulty, danger):.1f}%")

with open("risk_thresholds.json", "w", encoding="utf-8") as f:
    json.dump({
        "warning": warning,
        "danger": danger,
        "method": f"percentile {WARN_PCT}/{DANGER_PCT} of healthy engines (5-fold out-of-fold risk)",
        "healthy_flagged_warning_pct": round(share(healthy, warning), 1),
        "faulty_caught_warning_pct": round(share(faulty, warning), 1),
    }, f, ensure_ascii=False, indent=2)
print("\n💾 บันทึก risk_thresholds.json แล้ว รีสตาร์ต API เพื่อใช้เกณฑ์ใหม่")
