import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime
import re
import streamlit.components.v1 as components

--- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - Global Health AI", page_icon="🌍", layout="centered")

st.caption("⚠️ DISCLAIMER: Rakshak is an AI triage tool for informational purposes only. "
"It is NOT a medical diagnosis. In an emergency, call 102 (Ambulance) immediately.")

--- 2. INITIALIZE GLOBAL DATABASE ---
if 'logged_in' not in st.session_state:
st.session_state['logged_in'] = False
if 'user_profile' not in st.session_state:
st.session_state['user_profile'] = {"name": "", "email": "", "language": "English", "location": "Patna, India"}
if 'medical_history' not in st.session_state:
st.session_state['medical_history'] = []

--- 3. THE BRAIN SETUP (Raksha AI) ---
try:
API_KEY = st.secrets["AIzaSyBdCWfhzTx-qqS2AQatrMmA01FJAD1Uffo"]
except:
API_KEY = "PASTE_YOUR_KEY_HERE_IF_TESTING_LOCALLY"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def save_diagnosis(urgency, symptoms, ai_response):
entry = {
"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
"urgency": urgency,
"symptoms": symptoms[:100] + "...",
"full_report": ai_response
}
st.session_state['medical_history'].insert(0, entry)

--- 4. ONBOARDING & AUTHENTICATION SCREEN ---
if not st.session_state['logged_in']:
st.title("🌍 Welcome to Rakshak")

# 🌟 NEW: Interactive 3D Avatar embedded via Spline
st.markdown("### Meet Your AI Health Guardian")
components.html(
    """
    <iframe src='https://my.spline.design/robot-0b4cc5da82c5f7d391f1b29a2ee6f443/' frameborder='0' width='100%' height='300px'></iframe>
    """, height=300
)

st.write("Please sign in to securely save your history.")

col1, col2 = st.columns(2)
with col1:
    # These are prepped for Firebase/Supabase Auth integration
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
--- 5. MAIN APP INTERFACE ---
else:
tab_home, tab_history, tab_profile = st.tabs(["🏠 Home & Triage", "📜 My History", "👤 My Profile"])

user_lang = st.session_state['user_profile']['language']
user_loc = st.session_state['user_profile']['location']

with tab_home:
    st.title(f"Raksha is listening, {st.session_state['user_profile']['name']}.")
    
    input_method = st.radio("Choose input method:", ["📝 Text", "📸 Camera + Text"], horizontal=True)
    user_text = ""
    user_image = None
    
    if input_method == "📝 Text":
        user_text = st.text_area("Describe your symptoms in detail:")
    elif input_method == "📸 Camera + Text":
        user_image = st.camera_input("Take a photo of the issue")
        user_text = st.text_input("Add a brief description:")

    if st.button("🩺 Ask Raksha", type="primary"):
        if not (user_text or user_image):
            st.warning("Please provide details so Raksha can help you.")
        else:
            try:  
                with st.spinner("Raksha is analyzing..."):
                    # 🌟 NEW: Professional Prompt Engineering for Bullet Points
                    prompt = f"""
                    You are Raksha, an advanced global medical triage AI. 
                    Respond entirely in {user_lang}. The patient is currently in: {user_loc}.
                    
                    Format your response EXACTLY like this using clear Markdown bullet points:
                    **URGENCY:** [RED, YELLOW, or GREEN]
                    
                    **📝 SYMPTOMS SUMMARY:** * [Bullet point 1]
                    * [Bullet point 2]
                    
                    **⚕️ IMMEDIATE STEPS TO TAKE:** * [Action 1]
                    * [Action 2]
                    
                    **🏥 RECOMMENDED DOCTOR:** * [Type of Specialist]
                    
                    **💊 TREATMENT / ADVICE:**
                    * [Clear, actionable advice based on urgency]
                    """
                    
                    content = [prompt]
                    if user_text: content.append(f"Patient says: {user_text}")
                    if user_image: content.append(user_image)
                    
                    response = model.generate_content(content)
                    ai_response_text = response.text
                    
                    st.divider()
                    
                    # 🌟 NEW: The Bug Fix using Regex!
                    # This specifically looks for the word right after "URGENCY:"
                    match = re.search(r'\*\*URGENCY:\*\*\s*([A-Za-z]+)', ai_response_text, re.IGNORECASE)
                    
                    urgency = "GREEN" # Default fallback
                    if match:
                        extracted_word = match.group(1).upper()
                        if "RED" in extracted_word: urgency = "RED"
                        elif "YELLOW" in extracted_word: urgency = "YELLOW"
                        else: urgency = "GREEN"
                    
                    # Display colors accurately based on the exact parsed Urgency
                    if urgency == "RED":
                        st.error(ai_response_text)
                        st.error("🚨 This looks serious. Please seek medical attention.")
                    elif urgency == "YELLOW":
                        st.warning(ai_response_text)
                    else:
                        st.success(ai_response_text)
                    
                    save_diagnosis(urgency, user_text if user_text else "Media Input", ai_response_text)
                    
                    st.markdown("### 🏥 Next Steps")
                    col_share, col_action = st.columns(2)

                    with col_share:
                        share_text = urllib.parse.quote(f"Rakshak Health Alert for {st.session_state['user_profile']['name']}: {urgency} Alert.")
                        st.link_button("🔗 Share Report via WhatsApp", f"https://wa.me/?text={share_text}")

                    with col_action:
                        if urgency == "RED" or urgency == "YELLOW":
                            st.link_button("🩺 Consult a Doctor (Partner)", "https://apollo247.com", type="primary")
                        else:
                            st.link_button("💊 Order Essentials (1mg)", "https://1mg.com")

            except Exception as e:
                st.error(f"Raksha encountered an error: {e}")

with tab_history:
    st.title("📜 Medical History")
    if not st.session_state['medical_history']:
        st.info("No history found.")
    else:
        for entry in st.session_state['medical_history']:
            with st.expander(f"{entry['date']} | Status: {entry['urgency']}"):
                st.write(f"**Symptoms:** {entry['symptoms']}")
                st.write(f"**Report:**\n{entry['full_report']}")

with tab_profile:
    st.title("👤 My Profile")
    if st.button("🚪 Sign Out", type="primary"):
        st.session_state['logged_in'] = False
        st.rerun() 
