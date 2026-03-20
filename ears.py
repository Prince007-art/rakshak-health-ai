import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime
import re
import streamlit.components.v1 as components

# # --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - Global Health AI", page_icon="🌍", layout="centered")

# Disclaimer always at the top for safety
st.caption("⚠️ DISCLAIMER: Rakshak is an AI triage tool for informational purposes only. "
           "It is NOT a medical diagnosis. In an emergency, call 102 (Ambulance) immediately.")

# # --- 2. INITIALIZE GLOBAL DATABASE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {"name": "", "email": "", "language": "English", "location": "Patna, India"}
if 'medical_history' not in st.session_state:
    st.session_state['medical_history'] = []

# # --- 3. THE BRAIN SETUP (Raksha AI) ---
try:
    # We look for the LABEL "API_KEY" from your Streamlit Secrets
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("🚨 Configuration Error: Please check your API Key in Streamlit Secrets.")
    st.stop()

def save_diagnosis(urgency, symptoms, ai_response):
    entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "urgency": urgency,
        "symptoms": symptoms[:100] + "...",
        "full_report": ai_response
    }
    st.session_state['medical_history'].insert(0, entry)

# # --- 4. ONBOARDING & AUTHENTICATION SCREEN ---
if not st.session_state['logged_in']:
    st.title("🌍 Welcome to Rakshak")
    
    st.markdown("### Your AI Health Guardian is Ready")
    
    # NEW: Using a more stable, public 3D Avatar link
    components.html(
        """
        <iframe src='https://my.spline.design/clonemorphicheads-79693761358309f44f94025a4d6e901a/' frameborder='0' width='100%' height='300px'></iframe>
        """, height=300
    )
    
    st.write("Securely sign in to keep track of your health journey.")
    
    # Real-looking Login Buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🌐 Continue with Google", use_container_width=True):
            st.session_state['user_profile']['name'] = "Google User"
            st.session_state['logged_in'] = True
            st.rerun()
    with c2:
        if st.button("📘 Continue with Facebook", use_container_width=True):
            st.session_state['user_profile']['name'] = "FB User"
            st.session_state['logged_in'] = True
            st.rerun()
        
    st.divider()
    st.subheader("Or Quick Guest Access")
    with st.form("signup_form"):
        name = st.text_input("What should Raksha call you?")
        pref_lang = st.selectbox("Language", ["English", "हिन्दी (Hindi)", "Bhojpuri (भोजपुरी)"])
        location_input = st.text_input("Your City:", value="Patna, India")
        submit = st.form_submit_button("Launch Rakshak 🚀")
        
        if submit and name:
            st.session_state['user_profile']['name'] = name
            st.session_state['user_profile']['language'] = pref_lang
            st.session_state['user_profile']['location'] = location_input
            st.session_state['logged_in'] = True
            st.rerun()

# # --- 5. MAIN APP INTERFACE ---
else:
    tab_home, tab_history, tab_profile = st.tabs(["🏠 Health Triage", "📜 History", "👤 Profile"])
    
    user_lang = st.session_state['user_profile']['language']
    user_loc = st.session_state['user_profile']['location']
    
    with tab_home:
        st.title(f"Hello, {st.session_state['user_profile']['name']}!")
        
        # 🌟 FEATURE: Professional Multi-Input
        st.markdown("#### Describe your symptoms or upload a report")
        user_text = st.text_area("How are you feeling?", height=100, placeholder="E.g. I have a sharp pain in my lower back...")
        
        col_cam, col_file = st.columns(2)
        with col_cam:
            user_image = st.camera_input("📸 Scan Symptom")
        with col_file:
            uploaded_file = st.file_uploader("📂 Upload Doctor Report/Lab Result", type=['pdf', 'jpg', 'png', 'jpeg'])

        if st.button("🩺 Ask Raksha AI", type="primary", use_container_width=True):
            if not (user_text or user_image or uploaded_file):
                st.warning("Please provide some info so Raksha can help.")
            else:
                try:  
                    with st.spinner("Raksha is analyzing your data..."):
                        prompt = f"""
                        Act as Raksha, a professional medical triage AI. Respond in {user_lang}.
                        Current Location: {user_loc}.
                        
                        Give the answer in clear BULLET POINTS.
                        FORMAT:
                        **URGENCY:** [RED/YELLOW/GREEN]
                        **📝 SYMPTOMS SUMMARY:** [Bullet points]
                        **⚕️ ACTION STEPS:** [Bullet points]
                        **🏥 SPECIALIST NEEDED:** [Doctor type]
                        **💊 HOME ADVICE:** [Bullet points]
                        """
                        
                        inputs = [prompt, f"User notes: {user_text}"]
                        if user_image: inputs.append(user_image)
                        if uploaded_file: inputs.append(uploaded_file)
                        
                        response = model.generate_content(inputs)
                        ai_text = response.text
                        
                        # The Regex Fix for the Color Bug
                        match = re.search(r'URGENCY:\s*\**([A-Za-z]+)', ai_text, re.IGNORECASE)
                        urgency = "GREEN"
                        if match:
                            word = match.group(1).upper()
                            if "RED" in word: urgency = "RED"
                            elif "YELLOW" in word: urgency = "YELLOW"
                        
                        st.divider()
                        if urgency == "RED":
                            st.error(ai_text)
                            st.error("🚨 HIGH URGENCY: Consult a doctor immediately.")
                        elif urgency == "YELLOW":
                            st.warning(ai_text)
                        else:
                            st.success(ai_text)
                        
                        save_diagnosis(urgency, user_text if user_text else "Media/File Upload", ai_text)
                        
                        # Action Buttons
                        st.markdown("---")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.link_button("🔗 Share Report to WhatsApp", f"https://wa.me/?text=Rakshak%20Alert:%20{urgency}")
                        with c2:
                            link = "https://1mg.com" if urgency == "GREEN" else "https://apollo247.com"
                            st.link_button("🏥 Get Professional Help", link)

                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_history:
        st.header("Your Health Records")
        if not st.session_state['medical_history']:
            st.info("Your medical history will appear here.")
        else:
            for item in st.session_state['medical_history']:
                with st.expander(f"{item['date']} | {item['urgency']}"):
                    st.markdown(item['full_report'])

    with tab_profile:
        st.header("Profile Settings")
        st.write(f"**Name:** {st.session_state['user_profile']['name']}")
        st.write(f"**Default Location:** {st.session_state['user_profile']['location']}")
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
