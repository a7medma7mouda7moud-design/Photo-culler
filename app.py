import base64
import json
import io
from PIL import Image
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="AI Photo Culler", layout="wide", initial_sidebar_state="collapsed"
)

st.title("📸 مساعد فرز الصور الذكي (ChatGPT)")
st.caption("افرز صورك بذكاء من الآيفون باستعمال GPT-4o")

with st.sidebar:
  st.header("⚙️ الإعدادات")
  api_key = st.text_input("أدخل مفتاح OpenAI API Key:", type="password")
  st.markdown("[احصل على مفتاح من OpenAI](https://platform.openai.com/api-keys)")

if not api_key:
  st.info("👈 يُرجى إدخال OpenAI API Key من القائمة الجانبية (Sidebar) للبدء.")
  st.stop()

client = OpenAI(api_key=api_key)

uploaded_files = st.file_uploader(
    "اختر الصور من ألبوم الآيفون (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)


def encode_image(image):
  buffered = io.BytesIO()
  image.save(buffered, format="JPEG")
  return base64.b64encode(buffered.getvalue()).decode("utf-8")


if uploaded_files:
  if st.button(
      f"🚀 بدء تحليل {len(uploaded_files)} صورة", use_container_width=True
  ):
    results = []
    progress_bar = st.progress(0)

    prompt = """
        أنت خبير تقييم صور ومساعد فرز للمصورين المحترفين.
        قم بتحليل هذه الصورة بدقة شديدة وأخرج النتيجة بصيغة JSON حصراً باللغة العربية دون أي مقدمات أو كود فلوكس بالصيغة التالية:
        {
          "overall_score": 8.5,
          "category": "أفضل الصور",
          "strengths": ["نقطة 1", "نقطة 2"],
          "detailed_reason": "سبب التقييم",
          "suggested_improvements": ["تحسين 1", "تحسين 2"]
        }
        خيارات الفئة (category) المتاحة هي فقط: ("أفضل الصور", "تحتاج تعديل", "غير مناسبة")
        """

    for idx, file in enumerate(uploaded_files):
      img = Image.open(file).convert("RGB")
      img.thumbnail((1024, 1024))
      base64_img = encode_image(img)

      try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        },
                    },
                ],
            }],
        )

        data = json.loads(response.choices[0].message.content)
        data["file_name"] = file.name
        data["image"] = img
        results.append(data)

      except Exception as e:
        st.error(f"حدث خطأ أثناء تحليل {file.name}: {e}")

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
