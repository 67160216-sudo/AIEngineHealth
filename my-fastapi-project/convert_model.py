import pickle5 as pickle
import joblib

try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    # บันทึกกลับเป็นฟอร์แมตของเซิร์ฟเวอร์ปัจจุบัน
    joblib.dump(model, 'model_fixed.pkl')
    print("✅ แปลงไฟล์สำเร็จ! ได้ไฟล์ 'model_fixed.pkl'")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")