import json
import time
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Photo Culler", layout="wide", initial_sidebar_state="collapsed"
)

st.title("📸 مساعد فرز الصور الذكي")
st.caption("افرز صورك بذكاء من الآيفون واعرف أسباب التقييم بدقة")

with st.sidebar:
  st.header("⚙️ الإعدادات")
  api_key = st.text_input("أدخل مفتاح Gemini API Key:", type="password")
  st.markdown("[احصل على مفتاح مجاني من هنا](https://aistudio.google.com/)")

if not api_key:
  st.info("👈 يُرجى إدخال API Key من القائمة الجانبية (Sidebar) للبدء.")
  st.stop()

client = genai.Client(api_key=api_key)

uploaded_files = st.file_uploader(
    "اختر الصور من ألبوم الآيفون (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
  if st.button(
      f"🚀 بدء تحليل {len(uploaded_files)} صورة", use_container_width=True
  ):
    results = []
    progress_bar = st.progress(0)

    prompt = """
        أنت خبير تقييم صور ومساعد فرز للمصورين المحترفين.
        قم بتحليل هذه الصورة بدقة شديدة وأخرج النتيجة بصيغة JSON حصراً باللغة العربية.
        
        يجب أن يحتوي الـ JSON على:
        - overall_score: رقم من 10 (مثل 9.2)
        - category: اختر واحدة فقط من ("أفضل الصور", "تحتاج تعديل", "غير مناسبة")
        - strengths: قائمة بالنقاط القوية
        - detailed_reason: السبب الدقيق والواضح للتقييم.
        - suggested_improvements: قائمة بالتحسينات المقترحة.
        """

    for idx, file in enumerate(uploaded_files):
      img = Image.open(file)

      # تصغير أبعاد الصورة لتسريع التحليل وتوفير الكوتا
      img.thumbnail((1024, 1024))

      # إعادة المحاولة تلقائياً في حال وجود Rate Limit
      max_retries = 3
      for attempt in range(max_retries):
        try:
          response = client.models.generate_content(
              model="gemini-2.0-flash",
              contents=[img, prompt],
              config=types.GenerateContentConfig(
                  response_mime_type="application/json", temperature=0.2
              ),
          )
          data = json.loads(response.text)
          data["file_name"] = file.name
          data["image"] = img
          results.append(data)
          break
        except Exception as e:
          if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            if attempt < max_retries - 1:
              time.sleep(5)  # الانتظار 5 ثواني قبل إعادة المحاولة
              continue
          st.error(f"حدث خطأ أثناء تحليل {file.name}: {e}")

      # انتظار 3 ثوانٍ بين كل صورة والأخرى لتجنب تجاوز حد الطلبات
      time.sleep(3)
      progress_bar.progress((idx + 1) / len(uploaded_files))

    st.success("تم التحليل بنجاح!")
    st.divider()

    total = len(results)
    best = [r for r in results if r.get("category") == "أفضل الصور"]
    edit = [r for r in results if r.get("category") == "تحتاج تعديل"]
    bad = [r for r in results if r.get("category") == "غير مناسبة"]

    st.subheader("📊 Dashboard")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📂 إجمالي", total)
    m2.metric("✅ أفضل الصور", len(best))
    m3.metric("🟡 تحتاج تعديل", len(edit))
    m4.metric("🔴 غير مناسبة", len(bad))

    st.divider()
    st.subheader("🖼️ نتائج التحليل والتقييم")

    for res in results:
      with st.expander(
          f"📷 {res['file_name']} — ⭐ {res.get('overall_score', 'N/A')}/10"
      ):
        st.image(res["image"], use_container_width=True)
        st.markdown("**💬 سبب التقييم الدقيق:**")
        st.info(res.get("detailed_reason", "لا يوجد"))

        st.markdown("**💪 نقاط القوة:**")
        for s in res.get("strengths", []):
          st.write(f"- {s}")

        st.markdown("**🛠️ التحسينات المقترحة:**")
        for imp in res.get("suggested_improvements", []):
          st.write(f"- `{imp}`")
