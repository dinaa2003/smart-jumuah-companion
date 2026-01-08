
import streamlit as st
import sqlite3
import os
import datetime

# الاتصال بقاعدة البيانات
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
db_path = os.path.join(desktop_path, "Friday.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# إنشاء جدول المحادثة إذا لم يكن موجودًا
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    message TEXT,
    timestamp TEXT
)
""")
conn.commit()

# إعداد الصفحة
st.set_page_config(page_title="Smart Jumu’ah Companion", layout="centered")
st.title("📿 Smart Jumu’ah Companion")

# رسالة ترحيبية وتعليمات الاستخدام
welcome_message = """
### 🌙 Welcome to Smart Jumu’ah Companion

👉 To use this app, try typing one of the following keywords in the chat:

- "تفسير" / "tafsir" → for tafsir of a verse  
- "آية" / "ayah" → to display a verse  
- "دعاء" / "duaa" → to get a duaa  
- "حديث" / "hadith" → see hadiths in the tab  

📚 You can also explore Hadiths and Duas using the tabs above.
"""

arabic_message = """
### 🌙 مرحبًا بك في رفيق الجمعة الذكي

👉 لاستخدام التطبيق، جرب كتابة إحدى الكلمات التالية في المحادثة:

- "تفسير" → للحصول على تفسير آية  
- "آية" → لعرض آية من القرآن  
- "دعاء" → للحصول على دعاء  
- "حديث" → لعرض الأحاديث من التبويب المخصص  

📚 يمكنك أيضًا استكشاف الأحاديث والأدعية من خلال التبويبات أعلاه.
"""

# اختيار اللغة (مع key لتجنب DuplicateElementId)
language = st.radio("اختر اللغة / Choose Language", ["العربية", "English"], key="language_radio")
st.info(arabic_message if language == "العربية" else welcome_message)

# تهيئة الحالة
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "awaiting_tafsir" not in st.session_state:
    st.session_state.awaiting_tafsir = False
if "awaiting_ayah" not in st.session_state:
    st.session_state.awaiting_ayah = False
if "ayah_display" not in st.session_state:
    st.session_state.ayah_display = None

# دالة حفظ الرسائل
def save_message(role, message):
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO chat_log (role, message, timestamp) VALUES (?, ?, ?)", (role, message, timestamp))
    conn.commit()

# واجهة تبويبية
tab1, tab2, tab3 = st.tabs(["💬 المحادثة", "📜 الأحاديث", "🕊️ الأدعية"])

# 💬 تبويب المحادثة
with tab1:
    st.subheader("💬 المحادثة التفاعلية")

    # زر حذف المحادثة (مع key)
    if st.button("🗑️ حذف المحادثة", key="clear_chat"):
        st.session_state.chat_history = []
        st.session_state.ayah_display = None
        cursor.execute("DELETE FROM chat_log")
        conn.commit()
        st.success("✅ تم حذف المحادثة بنجاح.")

    # إدخال المستخدم
    user_input = st.chat_input("اكتب سؤالك هنا..." if language == "العربية" else "Type your question here...")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        save_message("user", user_input)
        st.session_state.message_count += 1

        # الصلاة على النبي
        if st.session_state.message_count % 3 == 0:
            salawat = "اللهم صلِّ على محمد وعلى آل محمد كما صليت على إبراهيم وعلى آل إبراهيم إنك حميد مجيد"
            st.session_state.chat_history.append(("assistant", f"🌸 {salawat}"))
            save_message("assistant", salawat)

        # طلب تفسير
        if ("تفسير" in user_input.lower() and language == "العربية") or ("tafsir" in user_input.lower() and language == "English"):
            st.session_state.awaiting_tafsir = True
            prompt = "أي آية تريد تفسيرها؟" if language == "العربية" else "Which verse would you like tafsir for?"
            st.session_state.chat_history.append(("assistant", prompt))

        elif st.session_state.awaiting_tafsir and user_input.isdigit():
            ayah_number = int(user_input)
            cursor.execute("SELECT arabic, english FROM tafsir WHERE ayah_number = ?", (ayah_number,))
            tafsir = cursor.fetchone()
            # تحقق من وجود نتيجة قبل الوصول للعناصر
            if tafsir:
                response = tafsir[0] if language == "العربية" else tafsir[1]
            else:
                response = "❗️لا يوجد تفسير لهذه الآية." if language == "العربية" else "❗️No tafsir available."
            st.session_state.chat_history.append(("assistant", f"🧠 {response}"))
            save_message("assistant", response)
            st.session_state.awaiting_tafsir = False

        # طلب آية كاملة
        elif ("آية" in user_input.lower() and language == "العربية") or ("ayah" in user_input.lower() and language == "English"):
            st.session_state.awaiting_ayah = True
            prompt = "أي رقم آية تريد عرضها؟" if language == "العربية" else "Which verse number would you like to see?"
            st.session_state.chat_history.append(("assistant", prompt))

        elif st.session_state.awaiting_ayah and user_input.isdigit():
            ayah_number = int(user_input)
            cursor.execute("SELECT arabic, english FROM ayahs WHERE ayah_number = ?", (ayah_number,))
            ayah = cursor.fetchone()
            cursor.execute("SELECT arabic, english FROM tafsir WHERE ayah_number = ?", (ayah_number,))
            tafsir = cursor.fetchone()
            # تحقق من وجود النتائج قبل الوصول للعناصر
            ayah_text = ayah[0] if (ayah and language == "العربية") else (ayah[1] if ayah else None) if language != "العربية" else None
            # أفضل شكل واضح:
            if ayah:
                ayah_text = ayah[0] if language == "العربية" else ayah[1]
            else:
                ayah_text = None
            if tafsir:
                tafsir_text = tafsir[0] if language == "العربية" else tafsir[1]
            else:
                tafsir_text = None
            st.session_state.ayah_display = {
                "ayah": ayah_text,
                "tafsir": tafsir_text
            }
            st.session_state.awaiting_ayah = False

        # دعاء
        elif ("دعاء" in user_input.lower() and language == "العربية") or ("duaa" in user_input.lower() and language == "English"):
            cursor.execute("SELECT arabic, english FROM duas ORDER BY RANDOM() LIMIT 1")
            dua = cursor.fetchone()
            if dua:
                response = dua[0] if language == "العربية" else dua[1]
            else:
                response = "❗️لا توجد أدعية متاحة." if language == "العربية" else "❗️No duaas available."
            st.session_state.chat_history.append(("assistant", f"🕊️ {response}"))
            save_message("assistant", response)

        # حديث
        elif ("حديث" in user_input.lower() and language == "العربية") or ("hadith" in user_input.lower() and language == "English"):
            msg = "📚 لعرض الأحاديث، اختر الموضوع من تبويب الأحاديث." if language == "العربية" else "📚 To view hadiths, use the Hadiths tab."
            st.session_state.chat_history.append(("assistant", msg))

        # fallback
        else:
            fallback = "🤔 لم أفهم، جرب أن تقول: تفسير، حديث، دعاء، أو آية." if language == "العربية" else "🤔 I didn’t understand. Try saying: tafsir, hadith, duaa, or ayah."
            st.session_state.chat_history.append(("assistant", fallback))

    # عرض المحادثة
    for role, msg in st.session_state.chat_history:
        st.chat_message(role).markdown(msg)

    # عرض الآية والتفسير في مساحة منفصلة
    if st.session_state.ayah_display:
        st.markdown("---")
        st.markdown("### 📖 الآية المطلوبة")
        st.success(st.session_state.ayah_display["ayah"] or ("❗️لا توجد آية بهذا الرقم." if language == "العربية" else "❗️No ayah found."))
        st.markdown("### 🧠 التفسير")
        st.info(st.session_state.ayah_display["tafsir"] or ("ℹ️ لا يوجد تفسير." if language == "العربية" else "ℹ️ No tafsir available."))

# 📜 تبويب الأحاديث
with tab2:
    st.subheader("📜 أحاديث الجمعة حسب الموضوع")
    cursor.execute("SELECT DISTINCT topic FROM hadiths")
    topics = [row[0] for row in cursor.fetchall()]
    if topics:
        selected_topic = st.selectbox("اختر موضوع الحديث", topics, key="hadith_topic")
        if st.button("عرض الحديث" if language == "العربية" else "Show Hadith", key="show_hadith"):
            cursor.execute("SELECT arabic, english, reference FROM hadiths WHERE topic = ?", (selected_topic,))
            hadiths = cursor.fetchall()
            if hadiths:
                for arabic, english, reference in hadiths:
                    st.markdown("---")
                    st.markdown(f"📖 {arabic}" if language == "العربية" else f"📖 {english}")
                    st.markdown(f"📚 المرجع: {reference}")
            else:
                st.info("لا يوجد أحاديث لهذا الموضوع." if language == "العربية" else "No hadiths found for this topic.")
    else:
        st.info("لا توجد أحاديث في قاعدة البيانات." if language == "العربية" else "No hadiths in the database.")

# 🕊️ تبويب الأدعية
with tab3:
    st.subheader("🕊️ أدعية يوم الجمعة")
    cursor.execute("SELECT arabic, english FROM duas")
    duas = cursor.fetchall()
    for arabic, english in duas:
        if language == "العربية":
            st.markdown(f"*📌 الدعاء:** {arabic}")
        else:
            st.markdown(f"*📌 Duaa:** {english}")