import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime
import re
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - Global AI Health", page_icon="🌍", layout="centered")

st.caption("⚠️ DISCLAIMER: Rakshak is an AI triage tool for informational purposes only. "
           "It is NOT a medical diagnosis. In an emergency, call 102 (Ambulance) immediately.")

# --- 2. INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {"name": "", "language": "English", "location": "Patna, India"}
if 'medical_history' not in st.session_state:
    st.session_state['medical_history'] = []

# --- 3. THE BRAIN SETUP ---
try:
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
    # Corrected model version
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("🚨 API Key Missing! Go to Streamlit Secrets and add 'API_KEY'.")
    st.stop()

def save_diagnosis(urgency, symptoms, ai_response):
    entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "urgency": urgency,
        "symptoms": symptoms[:100] + "...",
        "full_report": ai_response
    }
    st.session_state['medical_history'].insert(0, entry)

# --- 4. LOGIN / ONBOARDING ---
if not st.session_state['logged_in']:
    st.title("🌍 Welcome to Rakshak")
    st.markdown("### Your Global AI Health Guardian")
    
    # Swapped to a highly stable Spline URL to avoid 'Access Denied'
    components.html(
        """
        <iframe src='https://my.spline.design/clonemorphicheads-79693761358309f44f94025a4d6e901a/' frameborder='0' width='100%' height='300px'></iframe>
        """, height=300
    )
    
    col_g, col_f = st.columns(2)
    with col_g:
        if st.button("🌐 Continue with Google", use_container_width=True):
            st.session_state['user_profile']['name'] = "Google User"
            st.session_state['logged_in'] = True
            st.rerun()
    with col_f:
        if st.button("📘 Continue with Facebook", use_container_width=True):
            st.session_state['user_profile']['name'] = "Facebook User"
            st.session_state['logged_in'] = True
            st.rerun()

    st.divider()
    with st.form("guest_form"):
        st.subheader("Guest / Quick Setup")
        g_name = st.text_input("Name")
        g_lang = st.selectbox("Language", ["English", "हिन्दी (Hindi)", "Bhojpuri (भोजपुरी)"])
        g_loc = st.text_input("Location", value="Patna, India")
        if st.form_submit_button("Launch Rakshak 🚀") and g_name:
            st.session_state['user_profile'].update({"name": g_name, "language": g_lang, "location": g_loc})
            st.session_state['logged_in'] = True
            st.rerun()

# --- 5. MAIN APP INTERFACE ---
else:
    tab1, tab2, tab3 = st.tabs(["🩺 Health Triage", "📜 Medical History", "👤 Profile"])
    
    profile = st.session_state['user_profile']

    with tab1:
        st.title(f"Hello, {profile['name']}!")
        
        # All-in-one input section
        user_text = st.text_area("Describe your symptoms:", placeholder="E.g., I have a sharp pain in my chest...")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🎙️ Voice**")
            audio = st.audio_input("Record")
        with c2:
            st.markdown("**📸 Photo**")
            photo = st.camera_input("Scan")
        with c3:
            st.markdown("**📂 File**")
            report = st.file_uploader("Upload", type=['pdf', 'jpg', 'png'])

        if st.button("🩺 Ask Raksha AI", type="primary", use_container_width=True):
            if not (user_text or audio or photo or report):
                st.warning("Please provide some info (text, voice, or photo) for Raksha to analyze.")
            else:
                try:
                    with st.spinner("Analyzing your data..."):
                        # Stricter prompt to ensure the color-coding works perfectly
                        prompt = f"""
                        Role: Professional Medical Triage AI (Raksha).
                        Language: {profile['language']}. Location: {profile['location']}.
                        
                        Strict Format:
                        **URGENCY:** [RED/YELLOW/GREEN]
                        **📝 SUMMARY:** [Bullet points]
                        **⚕️ ACTIONS:** [Bullet points]
                        **🏥 SPECIALIST:** [Doctor type]
                        **💊 ADVICE:** [Bullet points]
                        """
                        
                        inputs = [prompt, f"User notes: {user_text}"]
                        if audio: inputs.append(audio)
                        if photo: inputs.append(photo)
                        if report: inputs.append(report)
                        
                        response = model.generate_content(inputs)
                        ai_text = response.text
                        
                        # Fix the "Color Mismatch" logic
                        clean_text = ai_text.upper()
                        if "**URGENCY:** RED" in clean_text: urgency = "RED"
                        elif "**URGENCY:** YELLOW" in clean_text: urgency = "YELLOW"
                        else: urgency = "GREEN"
                        
                        st.divider()
                        if urgency == "RED":
                            st.error(ai_text)
                            st.error("🚨 EMERGENCY: Consult a doctor immediately.")
                        elif urgency == "YELLOW":
                            st.warning(ai_text)
                        else:
                            st.success(ai_text)
                        
                        save_diagnosis(urgency, user_text if user_text else "Media/Voice Input", ai_text)
                        
                        # Next Steps & Download
                        c_wa, c_dl = st.columns(2)
                        with c_wa:
                            msg = urllib.parse.quote(f"Health Alert ({urgency}): {ai_text[:100]}...")
                            st.link_button("🔗 Share via WhatsApp", f"https://wa.me/?text={msg}")
                        with c_dl:
                            st.download_button("📥 Download Report", ai_text, file_name="rakshak_report.txt")

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    with tab2:
        st.header("Medical History")
        if not st.session_state['medical_history']:
            st.info("No records yet.")
        else:
            for item in st.session_state['medical_history']:
                # Ensure the bar color matches the stored urgency
                status_icon = "🔴" if item['urgency'] == "RED" else "🟡" if item['urgency'] == "YELLOW" else "🟢"
                with st.expander(f"{status_icon} {item['date']} | Status: {item['urgency']}"):
                    st.markdown(item['full_report'])
                    st.download_button("Download this record", item['full_report'], file_name=f"report_{item['date']}.txt")

    with tab3:
        st.header("Profile Settings")
        st.write(f"**Name:** {profile['name']}")
        st.write(f"**Language:** {profile['language']}")
        st.write(f"**Location:** {profile['location']}")
        if st.button("🚪 Log Out", type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()
