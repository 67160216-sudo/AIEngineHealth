# -*- coding: utf-8 -*-
"""
engine_ai.py
ส่วนจัดการโมเดล AI ทั้งหมด (โหลดโมเดล + ประเมินความเสี่ยง)
แยกออกจาก main.py เพื่อให้ทดสอบได้ง่าย และ main.py เหลือแค่เรื่อง API
"""
import json
import os
from typing import Dict, List, Optional

import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "engine_model.pkl")
# ถ้ามีไฟล์นี้ (สร้างโดย calibrate_thresholds.py) จะใช้เกณฑ์จากไฟล์นี้ก่อน
THRESHOLD_FILE = os.path.join(BASE_DIR, "risk_thresholds.json")

# เกณฑ์สถานะ (ความเสี่ยง %)
# - 50% คือจุดตัดสินใจของโมเดล (เทรนแบบ class_weight="balanced")
#   ต่ำกว่านี้ = โมเดลเอนไปทาง "ปกติ"
# - 70% ขึ้นไป = โมเดลมั่นใจค่อนข้างสูงว่ามีปัญหา
# ถ้าตั้งเป็น None จะใช้ค่าที่บันทึกไว้ในไฟล์โมเดลแทน
RISK_THRESHOLDS_OVERRIDE: Optional[Dict[str, float]] = {"warning": 50.0, "danger": 70.0}

# ชื่อภาษาไทยและหน่วย (ใช้ในข้อความเตือน)
FEATURE_LABELS = {
    "engine_rpm": ("รอบเครื่องยนต์", "rpm"),
    "lub_oil_pressure": ("แรงดันน้ำมันหล่อลื่น", "bar"),
    "fuel_pressure": ("แรงดันเชื้อเพลิง", "bar"),
    "coolant_pressure": ("แรงดันน้ำหล่อเย็น", "bar"),
    "lub_oil_temp": ("อุณหภูมิน้ำมันหล่อลื่น", "°C"),
    "coolant_temp": ("อุณหภูมิน้ำหล่อเย็น", "°C"),
}


# ==============================================================================
# กฎตามหลักวิศวกรรมยานยนต์ (Rule-based) ใช้ร่วมกับ AI
# ค่าเกณฑ์เป็นแนวทางทั่วไปของเครื่องยนต์เบนซิน/ดีเซลรถยนต์ ไม่ได้มาจากชุดข้อมูล
# ปรับได้ที่นี่ที่เดียว
# ==============================================================================
RULES = {
    "coolant_temp":     {"caution_above": 105.0, "critical_above": 115.0},   # °C
    "lub_oil_temp":     {"caution_above": 110.0, "critical_above": 125.0},   # °C
    "lub_oil_pressure": {"critical_below": 0.5,                              # bar
                         "bar_per_1000rpm": 0.7,                             # ~10 psi ต่อ 1000 rpm
                         "caution_above": 7.0},
    "engine_rpm":       {"caution_above": 6500.0, "critical_above": 7500.0}, # rpm
}

# ความเสี่ยงขั้นต่ำเมื่อพบความผิดปกติตามกฎ (ทำให้ผลไม่ต่ำเกินจริง)
RULE_RISK_FLOOR = {"caution": 60.0, "critical": 85.0}


def engineering_checks(v: Dict[str, float], peak_rpm: Optional[float] = None) -> List[dict]:
    """ตรวจค่าเซนเซอร์ตามหลักวิศวกรรม คืนรายการสิ่งที่พบ (level: caution / critical)
    peak_rpm = รอบสูงสุดระหว่างขับ (ถ้ามี) ใช้ตรวจ Red line แทนรอบขณะเดินเบา"""
    found = []

    def add(feature, level, message):
        found.append({"feature": feature, "level": level, "message": message})

    ct, r = v["coolant_temp"], RULES["coolant_temp"]
    if ct > r["critical_above"]:
        add("coolant_temp", "critical", f"อุณหภูมิน้ำหล่อเย็น {ct:g} °C สูงเกิน {r['critical_above']:g} °C เสี่ยงเครื่องยนต์ร้อนจัด (Overheat) ควรหยุดใช้งานและตรวจระบบระบายความร้อน")
    elif ct > r["caution_above"]:
        add("coolant_temp", "caution", f"อุณหภูมิน้ำหล่อเย็น {ct:g} °C สูงกว่าช่วงทำงานปกติ (ประมาณ 85–105 °C) ควรตรวจหม้อน้ำ พัดลม และวาล์วน้ำ")

    ot, r = v["lub_oil_temp"], RULES["lub_oil_temp"]
    if ot > r["critical_above"]:
        add("lub_oil_temp", "critical", f"อุณหภูมิน้ำมันหล่อลื่น {ot:g} °C สูงเกิน {r['critical_above']:g} °C น้ำมันเสื่อมสภาพเร็ว เสี่ยงชิ้นส่วนสึกหรอ")
    elif ot > r["caution_above"]:
        add("lub_oil_temp", "caution", f"อุณหภูมิน้ำมันหล่อลื่น {ot:g} °C ค่อนข้างสูง ควรตรวจระดับและสภาพน้ำมันเครื่อง")

    op, rpm, r = v["lub_oil_pressure"], v["engine_rpm"], RULES["lub_oil_pressure"]
    need = r["bar_per_1000rpm"] * rpm / 1000
    if op < r["critical_below"]:
        add("lub_oil_pressure", "critical", f"แรงดันน้ำมันหล่อลื่น {op:g} bar ต่ำมาก เสี่ยงเครื่องยนต์ขาดการหล่อลื่น ควรดับเครื่องและตรวจระดับน้ำมัน/ปั๊มน้ำมันทันที")
    elif op < need:
        add("lub_oil_pressure", "caution", f"แรงดันน้ำมันหล่อลื่น {op:g} bar ต่ำกว่าที่ควรเป็นที่ {rpm:g} rpm (ควรมีอย่างน้อยประมาณ {need:.1f} bar)")
    elif op > r["caution_above"]:
        add("lub_oil_pressure", "caution", f"แรงดันน้ำมันหล่อลื่น {op:g} bar สูงผิดปกติ อาจมีการอุดตันหรือวาล์วระบายแรงดันผิดปกติ")

    er, r = (peak_rpm if peak_rpm is not None else v["engine_rpm"]), RULES["engine_rpm"]
    what = "รอบสูงสุดขณะขับ" if peak_rpm is not None else "รอบเครื่องยนต์"
    if er > r["critical_above"]:
        add("engine_rpm", "critical", f"{what} {er:,.0f} rpm เกินช่วงปลอดภัยของรถยนต์ทั่วไป (Red line) เสี่ยงความเสียหายรุนแรง")
    elif er > r["caution_above"]:
        add("engine_rpm", "caution", f"{what} {er:,.0f} rpm สูงใกล้ Red line ไม่ควรใช้งานต่อเนื่อง")

    return found


class EngineAI:
    def __init__(self, model_file: str = MODEL_FILE):
        self.bundle = None
        self.error: Optional[str] = None
        self.calibrated: Optional[Dict[str, float]] = None
        if os.path.exists(THRESHOLD_FILE):
            try:
                with open(THRESHOLD_FILE, encoding="utf-8") as f:
                    t = json.load(f)
                self.calibrated = {"warning": float(t["warning"]), "danger": float(t["danger"])}
                print(f"✅ ใช้เกณฑ์จาก risk_thresholds.json: {self.calibrated}")
            except Exception as e:
                print(f"⚠️ อ่าน risk_thresholds.json ไม่ได้ ใช้เกณฑ์ค่าเริ่มต้นแทน: {e}")
        try:
            self.bundle = joblib.load(model_file)
            print(f"✅ โหลดโมเดล {os.path.basename(model_file)} "
                  f"({self.bundle['metrics']['model']}) เรียบร้อยแล้ว")
        except Exception as e:
            self.error = str(e)
            print(f"❌ โหลดโมเดลไม่สำเร็จ: {e}")

    @property
    def ready(self) -> bool:
        return self.bundle is not None

    @property
    def features(self) -> List[str]:
        return self.bundle["features"]

    @property
    def thresholds(self) -> Dict[str, float]:
        return self.calibrated or RISK_THRESHOLDS_OVERRIDE or self.bundle["risk_thresholds"]

    def status_from_risk(self, risk: float) -> str:
        t = self.thresholds
        if risk >= t["danger"]:
            return "danger"
        if risk >= t["warning"]:
            return "warning"
        return "normal"

    def range_warnings(self, values: Dict[str, float]) -> List[dict]:
        """เตือนเมื่อค่าที่กรอกอยู่นอกช่วง 1%-99% ของข้อมูลที่ใช้เทรน
        (นอกช่วงนี้โมเดลแทบไม่เคยเห็น ผลจึงเชื่อถือได้น้อยลง)"""
        warnings = []
        for f in self.features:
            stats = self.bundle["feature_stats"][f]
            v = values[f]
            label, unit = FEATURE_LABELS.get(f, (f, ""))
            if v < stats["p01"]:
                direction = "ต่ำ"
            elif v > stats["p99"]:
                direction = "สูง"
            else:
                continue
            warnings.append({
                "feature": f,
                "message": f"{label} {v:g} {unit} {direction}กว่าช่วงที่พบในข้อมูล "
                           f"({stats['p01']:g}–{stats['p99']:g} {unit}) ผลประเมินอาจคลาดเคลื่อน",
            })
        return warnings

    def predict(self, values: Dict[str, float], peak_rpm: Optional[float] = None) -> dict:
        """values: dict ที่มี key ครบตาม self.features"""
        if not self.ready:
            raise RuntimeError(f"โมเดลยังไม่พร้อมใช้งาน: {self.error}")

        row = pd.DataFrame([{f: float(values[f]) for f in self.features}])[self.features]
        proba_faulty = float(self.bundle["model"].predict_proba(row)[0, 1])
        ai_risk = round(proba_faulty * 100, 1)

        # รวมผล: ใช้ AI เป็นหลัก แต่ถ้ากฎวิศวกรรมพบความผิดปกติ ความเสี่ยงต้องไม่ต่ำกว่าเกณฑ์ขั้นต่ำ
        findings = engineering_checks(values, peak_rpm)
        # ค่าขั้นต่ำต้องอยู่ในโซนที่ถูกต้องเสมอ แม้เกณฑ์จะถูกปรับจากการ calibrate
        t = self.thresholds
        floors = {
            "caution": min(99.0, max(RULE_RISK_FLOOR["caution"], t["warning"] + 5)),
            "critical": min(99.0, max(RULE_RISK_FLOOR["critical"], t["danger"] + 5)),
        }
        floor = 0.0
        for fd in findings:
            floor = max(floor, floors[fd["level"]])
        risk = round(max(ai_risk, floor), 1)

        return {
            "risk_percent": risk,
            "ai_risk_percent": ai_risk,
            "health_percent": round(100 - risk, 1),
            "status": self.status_from_risk(risk),
            "adjusted_by_rules": risk > ai_risk,
            "findings": findings,
            "warnings": self.range_warnings(values),
        }

    def info(self) -> dict:
        """ข้อมูลโมเดลสำหรับหน้าเว็บ (ช่วงค่าฟอร์ม, เกณฑ์, ผลการวัด)"""
        if not self.ready:
            return {"ready": False, "error": self.error}
        return {
            "ready": True,
            "features": [
                {
                    "key": f,
                    "label": FEATURE_LABELS.get(f, (f, ""))[0],
                    "unit": FEATURE_LABELS.get(f, (f, ""))[1],
                    **self.bundle["feature_stats"][f],
                }
                for f in self.features
            ],
            "thresholds": self.thresholds,
            "metrics": self.bundle["metrics"],
            "trained_at": self.bundle.get("trained_at"),
        }
