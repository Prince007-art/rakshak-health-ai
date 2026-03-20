import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime
import re
import streamlit.components.v1 as components

# # --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - AI Health", page_icon="🌍", layout="centered")

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
    # Looks for the LABEL "API_KEY" in Streamlit Secrets
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("🚨 API Key Missing! Please add 'API_KEY' to your Streamlit Secrets.")
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
    
    st.markdown("### Meet Your AI Health Guardian")
    
    # 🌟 FIXED: Stable Public 3D Avatar (Spline)
    components.html(
        """
        <iframe src='https://my.spline.design/glassiconscopy-3759a20228d447f5264b383794b638a1/' frameborder='0' width='100%' height='300px'></iframe>
        """, height=300
    )
    
    st.write("Sign in to securely save your medical history.")
    
    # Professional Mock Login Buttons
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
    st.subheader("Or Use Guest Setup")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        pref_lang = st.selectbox("Preferred Language", ["English", "हिन्दी (Hindi)", "Bhojpuri (भोजपुरी)"])
        location_input = st.text_input("City/Location:", value="Patna, India")
        submit = st.form_submit_button("Start Using Rakshak")
        
        if submit and name:
            st.session_state['user_profile']['name'] = name
            st.session_state['user_profile']['language'] = pref_lang
            st.session_state['user_profile']['location'] = location_input
            st.session_state['logged_in'] = True
            st.rerun()

# # --- 5. MAIN APP INTERFACE ---
else:
    tab_home, tab_history, tab_profile = st.tabs(["🏠 Home & Triage", "📜 My History", "👤 My Profile"])
    
    user_lang = st.session_state['user_profile']['language']
    user_loc = st.session_state['user_profile']['location']
    
    with tab_home:
        st.title(f"Raksha is listening, {st.session_state['user_profile']['name']}.")
        
        # 🌟 NEW: All-in-One Professional Input
        st.markdown("#### How can Raksha help you today?")
        
        user_text = st.text_area("Describe symptoms:", placeholder="E.g. I have a headache and feel nauseous.")
        
        # Layout for Media Inputs
        col_mic, col_cam, col_file = st.columns(3)
        with col_mic:
            st.write("🎙️ Voice Input")
            audio_file = st.audio_input("Record symptoms")
        with col_cam:
            st.write("📸 Scan Symptom")
            user_image = st.camera_input("Take photo")
        with col_file:
            st.write("📂 Upload Report")
            uploaded_file = st.file_uploader("PDF/Image", type=['pdf', 'jpg', 'png', 'jpeg'])

        if st.button("🩺 Ask Raksha AI", type="primary", use_container_width=True):
            if not (user_text or audio_file or user_image or uploaded_file):
                st.warning("Please provide information via text, voice, or photo.")
            else:
                try:  
                    with st.spinner("Raksha is analyzing..."):
                        prompt = f"""
                        You are Raksha, an advanced medical triage AI. Respond in {user_lang}. 
                        The patient is in {user_loc}.
                        
                        Format your response using Markdown bullet points:
                        **URGENCY:** [RED, YELLOW, or GREEN]
                        
                        **📝 SUMMARY:**
                        * [Bullet point list of what you found]
                        
                        **⚕️ IMMEDIATE STEPS:**
                        * [Actionable steps]
                        
                        **🏥 RECOMMENDED SPECIALIST:**
                        * [Doctor type]
                        
                        **💊 ADVICE:**
                        * [Clear, professional advice]
                        """
                        
                        # Pack all inputs for the AI
                        content_list = [prompt, f"User notes: {user_text}"]
                        if audio_file: content_list.append(audio_file)
                        if user_image: content_list.append(user_image)
                        if uploaded_file: content_list.append(uploaded_file)
                        
                        response = model.generate_content(content_list)
                        ai_text = response.text
                        
                        # Regex Fix for the "Red/Green" Bug
                        match = re.search(r'URGENCY:\s*\**([A-Za-z]+)', ai_text, re.IGNORECASE)
                        urgency = "GREEN"
                        if match:
                            word = match.group(1).upper()
                            if "RED" in word: urgency = "RED"
                            elif "YELLOW" in word: urgency = "YELLOW"
                        
                        st.divider()
                        if urgency == "RED":
                            st.error(ai_text)
                            st.error("🚨 HIGH URGENCY: Please seek medical help immediately.")
                        elif urgency == "YELLOW":
                            st.warning(ai_text)
                        else:
                            st.success(ai_text)
                        
                        save_diagnosis(urgency, user_text if user_text else "Voice/Media Input", ai_text)
                        
                        # Action Buttons
                        st.markdown("---")
                        c_wa, c_doc = st.columns(2)
                        with c_wa:
                            share = urllib.parse.quote(f"Rakshak Alert for {st.session_state['user_profile']['name']}: {urgency}")
                            st.link_button("🔗 WhatsApp Report", f"https://wa.me/?text={share}")
                        with c_doc:
                            link = "https://apollo247.com" if urgency != "GREEN" else "https://1mg.com"
                            st.link_button("🏥 Consult Doctor", link)

                except Exception as e:
                    st.error(f"Analysis Error: {e}")

    with tab_history:
        st.header("📜 Past Records")
        if not st.session_state['medical_history']:
            st.info("No records yet.")
        else:
            for item in st.session_state['medical_history']:
                with st.expander(f"{item['date']} | {item['urgency']}"):
                    st.markdown(item['full_report'])

    with tab_profile:
        st.header("👤 Your Profile")
        st.write(f"**Name:** {st.session_state['user_profile']['name']}")
        st.write(f"**Location:** {st.session_state['user_profile']['location']}")
        if st.button("🚪 Log Out", type="primary"):
            st.session_state['logged_in'] = False
            st.rerun() 
