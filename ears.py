import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime
import re
import streamlit.components.v1 as components

# # --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - Global Health AI", page_icon="🌍", layout="centered")

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
# SECURE WAY: Use the name "API_KEY" here. Set the actual value in Streamlit Secrets dashboard.
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "PASTE_KEY_ONLY_FOR_OFFLINE_TESTING" 

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Using the stable flash model

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
    components.html(
        """
        <iframe src='https://my.spline.design/robot-0b4cc5da82c5f7d391f1b29a2ee6f443/' frameborder='0' width='100%' height='300px'></iframe>
        """, height=300
    )
    
    st.write("Please sign in to securely save your history.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 Continue with Google (Mock)", use_container_width=True):
            st.session_state['user_profile']['name'] = "Guest User"
            st.session_state['logged_in'] = True
            st.rerun()
    with col2:
        st.button("📘 Continue with Facebook (Mock)", use_container_width=True)
        
    st.divider()
    st.subheader("Guest / Quick Setup")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        pref_lang = st.selectbox("Preferred Language", ["English", "हिन्दी (Hindi)", "Bhojpuri (भोजपुरी)"])
        location_input = st.text_input("City/Location:", placeholder="e.g., Patna, India")
        submit = st.form_submit_button("Start Using Rakshak")
        
        if submit and name:
            st.session_state['user_profile']['name'] = name
            st.session_state['user_profile']['language'] = pref_lang
            st.session_state['user_profile']['location'] = location_input if location_input else "Global"
            st.session_state['logged_in'] = True
            st.rerun()

# # --- 5. MAIN APP INTERFACE ---
else:
    tab_home, tab_history, tab_profile = st.tabs(["🏠 Home & Triage", "📜 My History", "👤 My Profile"])
    
    user_lang = st.session_state['user_profile']['language']
    user_loc = st.session_state['user_profile']['location']
    
    with tab_home:
        st.title(f"Raksha is listening, {st.session_state['user_profile']['name']}.")
        
        # 🌟 UPDATED: Professional Input Methods
        input_method = st.radio("Add details via:", ["📝 Text & Reports", "📸 Quick Photo"], horizontal=True)
        user_text = ""
        user_image = None
        uploaded_report = None
        
        if input_method == "📝 Text & Reports":
            user_text = st.text_area("Describe symptoms/concerns:", placeholder="Example: I've had a cough for 3 days and feel feverish.")
            uploaded_report = st.file_uploader("📂 Upload Medical Report (PDF or Image)", type=['pdf', 'jpg', 'png', 'jpeg'])
        elif input_method == "📸 Quick Photo":
            user_image = st.camera_input("Take a photo of the symptom or medicine")
            user_text = st.text_input("Briefly describe what we're looking at:")

        if st.button("🩺 Ask Raksha", type="primary"):
            if not (user_text or user_image or uploaded_report):
                st.warning("Please provide some information for Raksha to analyze.")
            else:
                try:  
                    with st.spinner("Raksha is analyzing..."):
                        prompt = f"""
                        You are Raksha, an advanced medical triage AI. Respond in {user_lang}. 
                        Current location: {user_loc}.
                        
                        Format your response using Markdown bullet points:
                        **URGENCY:** [RED, YELLOW, or GREEN]
                        
                        **📝 SUMMARY:**
                        * [Bullet points]
                        
                        **⚕️ IMMEDIATE STEPS:**
                        * [Bullet points]
                        
                        **🏥 RECOMMENDED SPECIALIST:**
                        * [Doctor type]
                        
                        **💊 ADVICE:**
                        * [Actionable advice]
                        """
                        
                        # Prepare data for AI
                        content_list = [prompt, f"User Input: {user_text}"]
                        if user_image: content_list.append(user_image)
                        if uploaded_report: content_list.append(uploaded_report)
                        
                        response = model.generate_content(content_list)
                        ai_response_text = response.text
                        
                        st.divider()
                        
                        # 🌟 FIXED: Accurate Regex for Urgency
                        match = re.search(r'URGENCY:\s*\**([A-Za-z]+)', ai_response_text, re.IGNORECASE)
                        urgency = "GREEN"
                        if match:
                            word = match.group(1).upper()
                            if "RED" in word: urgency = "RED"
                            elif "YELLOW" in word: urgency = "YELLOW"
                        
                        if urgency == "RED":
                            st.error(ai_response_text)
                            st.error("🚨 EMERGENCY: Please visit a hospital immediately.")
                        elif urgency == "YELLOW":
                            st.warning(ai_response_text)
                        else:
                            st.success(ai_response_text)
                        
                        save_diagnosis(urgency, user_text if user_text else "File Upload", ai_response_text)
                        
                        st.markdown("### 🏥 Next Steps")
                        c1, c2 = st.columns(2)
                        with c1:
                            share_text = urllib.parse.quote(f"Health Alert for {st.session_state['user_profile']['name']}: {urgency}")
                            st.link_button("🔗 Share via WhatsApp", f"https://wa.me/?text={share_text}")
                        with c2:
                            if urgency in ["RED", "YELLOW"]:
                                st.link_button("🩺 Online Consultation", "https://apollo247.com", type="primary")
                            else:
                                st.link_button("💊 Order Medicine", "https://1mg.com")

                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_history:
        st.title("📜 Medical History")
        if not st.session_state['medical_history']:
            st.info("No records yet.")
        else:
            for entry in st.session_state['medical_history']:
                with st.expander(f"{entry['date']} | {entry['urgency']}"):
                    st.write(f"**Brief:** {entry['symptoms']}")
                    st.write(entry['full_report'])

    with tab_profile:
        st.title("👤 My Profile")
        st.write(f"**User:** {st.session_state['user_profile']['name']}")
        st.write(f"**Language:** {st.session_state['user_profile']['language']}")
        if st.button("🚪 Sign Out"):
            st.session_state['logged_in'] = False
            st.rerun() 
