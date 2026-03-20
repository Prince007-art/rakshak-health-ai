import streamlit as st
import google.generativeai as genai
import urllib.parse
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rakshak - Global Health AI", page_icon="🌍", layout="centered")

# --- 2. INITIALIZE GLOBAL DATABASE (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {"name": "", "email": "", "language": "English", "location": "Patna, India"}
if 'medical_history' not in st.session_state:
    st.session_state['medical_history'] = []

# --- 3. THE BRAIN SETUP (Raksha AI) ---
# ⚠️ REMINDER: Move this to st.secrets before making it public for safety!
API_KEY = "AIzaSyCOdLiQv2Yp6oUxhEAWxqgb53mCbvDDqgs" 
genai.configure(api_key=API_KEY)
# CORRECTED: Changed to the active model version
model = genai.GenerativeModel('gemini-2.5-flash')

# Helper function to save history
def save_diagnosis(urgency, symptoms, ai_response):
    entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "urgency": urgency,
        "symptoms": symptoms[:100] + "...",
        "full_report": ai_response
    }
    st.session_state['medical_history'].insert(0, entry)

# --- 4. ONBOARDING & AUTHENTICATION SCREEN ---
if not st.session_state['logged_in']:
    st.title("🌍 Welcome to Rakshak")
    st.markdown("### Your Global AI Health Guardian")
    st.write("Please sign in to securely save your history and personalize your experience.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 Continue with Google", use_container_width=True):
            st.session_state['user_profile']['name'] = "Guest User"
            st.session_state['logged_in'] = True
            st.rerun()
        st.button("📘 Continue with Facebook", use_container_width=True)
    with col2:
        st.button("📱 Continue with Phone", use_container_width=True)
        st.button("✉️ Continue with Email", use_container_width=True)
    
    st.divider()
    st.subheader("Guest / Quick Setup")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        
        # Global Languages
        languages = ["English", "Español (Spanish)", "Français (French)", "हिन्दी (Hindi)", 
                     "العربية (Arabic)", "中文 (Mandarin)", "Português (Portuguese)", "Русский (Russian)", "Bhojpuri (भोजपुरी)"]
        pref_lang = st.selectbox("Preferred Language", languages)
        
        # Location Permission Mock
        st.write("📍 **Location Services**")
        loc_permission = st.checkbox("Allow Rakshak to access your location via Google Maps.")
        location_input = st.text_input("Or type your current city/country manually:", placeholder="e.g., Patna, India")
        
        submit = st.form_submit_button("Start Using Rakshak")
        
        if submit and name:
            st.session_state['user_profile']['name'] = name
            st.session_state['user_profile']['language'] = pref_lang
            if loc_permission and not location_input:
                st.session_state['user_profile']['location'] = "Auto-Detected (GPS Active)"
            else:
                st.session_state['user_profile']['location'] = location_input if location_input else "Global"
            
            st.session_state['logged_in'] = True
            st.rerun()

# --- 5. MAIN APP INTERFACE (Logged In) ---
else:
    # Top Navigation Bar using Tabs
    tab_home, tab_history, tab_profile = st.tabs(["🏠 Home & Triage", "📜 My History", "👤 My Profile"])
    
    user_lang = st.session_state['user_profile']['language']
    user_loc = st.session_state['user_profile']['location']
    
    # ==========================================
    # TAB 1: HOME & TRIAGE
    # ==========================================
    with tab_home:
        st.title(f"Raksha AI is listening, {st.session_state['user_profile']['name']}.")
        
        # Global/Regional Health News Alert
        st.info(f"📰 **Local Health Alert for {user_loc}:** Stay updated on seasonal trends in your region. Wash hands frequently.")
        
        st.markdown("### How can I help you today?")
        
        # Multimodal Inputs
        input_method = st.radio("Choose input method:", ["📝 Text", "🎤 Audio", "📸 Camera + Text"], horizontal=True)
        
        user_text = ""
        user_audio = None
        user_image = None
        
        if input_method == "📝 Text":
            user_text = st.text_area("Describe your symptoms in detail:")
        elif input_method == "🎤 Audio":
            user_audio = st.audio_input("Record your symptoms:")
        elif input_method == "📸 Camera + Text":
            user_image = st.camera_input("Take a photo of the issue (rash, wound, etc.)")
            user_text = st.text_input("Add a brief description:")

        # --- THE CORRECTED RAKSHA BUTTON BLOCK ---
        if st.button("🩺 Ask Raksha", type="primary"):
            if not (user_text or user_audio or user_image):
                st.warning("Please provide text, audio, or an image so Raksha can help you.")
            elif API_KEY == "YOUR_API_KEY_HERE":
                st.error("Please add your API Key to the code first!")
            else:
                try:  
                    with st.spinner("Raksha is analyzing your symptoms globally..."):
                        prompt = f"""
                        You are Raksha, an advanced global medical triage AI. 
                        Respond entirely in {user_lang}. The patient is currently in: {user_loc}.
                        
                        Format your response EXACTLY like this:
                        **URGENCY:** [RED, YELLOW, or GREEN]
                        **SYMPTOMS:** [Summary]
                        **WHAT TO DO:** [Immediate steps]
                        **WHICH DOCTOR TO CONSULT:** [Specialist]
                        
                        **TREATMENT / ADVICE:**
                        - If RED/YELLOW: Provide FIRST AID.
                        - If GREEN: Provide HOME REMEDIES for {user_loc}.
                        """
                        
                        # Prepare the inputs for the AI
                        content = [prompt]
                        if user_text: content.append(f"Patient says: {user_text}")
                        if user_audio: content.append({"mime_type": "audio/wav", "data": user_audio.read()})
                        if user_image: content.append(user_image)
                        
                        # The Live API Call
                        response = model.generate_content(content)
                        ai_response_text = response.text
                        
                        # Display results based on Urgency
                        st.divider()
                        urgency = "GREEN" # Default
                        
                        if "RED" in ai_response_text.upper():
                            st.error(ai_response_text)
                            st.error("🚨 This looks serious.")
                            urgency = "RED"
                        elif "YELLOW" in ai_response_text.upper():
                            st.warning(ai_response_text)
                            urgency = "YELLOW"
                        else:
                            st.success(ai_response_text)
                            urgency = "GREEN"
                        
                        # Save to history
                        save_diagnosis(urgency, user_text if user_text else "Media Input", ai_response_text)
                        
                        # CORRECTED: Monetization & Actions block is now properly indented inside the try block
                        st.caption("⚠️ DISCLAIMER: Rakshak is an AI triage tool for informational purposes only. "
                                   "It is NOT a medical diagnosis. In an emergency, call 102 (Ambulance) immediately.")

                        st.markdown("### 🏥 Next Steps for Your Health")
                        col_share, col_action = st.columns(2)

                        with col_share:
                            share_text = urllib.parse.quote(f"Rakshak Health Alert for {st.session_state['user_profile']['name']}: {urgency} Alert.")
                            st.link_button("🔗 Share Report via WhatsApp", f"https://wa.me/?text={share_text}")

                        with col_action:
                            if urgency == "RED" or urgency == "YELLOW":
                                doctor_link = "https://your-affiliate-link-to-apollo-or-practo.com"
                                st.link_button("🩺 Consult a Doctor (₹149 onwards)", doctor_link, type="primary")
                            else:
                                store_link = "https://your-affiliate-link-to-tata1mg.com"
                                st.link_button("💊 Order Essentials (1mg)", store_link)

                except Exception as e:
                    st.error(f"Raksha encountered an error: {e}")

    # ==========================================
    # TAB 2: MY HISTORY
    # ==========================================
    with tab_history:
        st.title("📜 Medical History")
        st.write("Your past interactions with Raksha are securely saved here.")
        
        if not st.session_state['medical_history']:
            st.info("No history found. Your future diagnoses will appear here.")
        else:
            for entry in st.session_state['medical_history']:
                with st.expander(f"{entry['date']} | Status: {entry['urgency']}"):
                    st.write(f"**Symptoms:** {entry['symptoms']}")
                    st.write(f"**Raksha's Report:**\n{entry['full_report']}")

    # ==========================================
    # TAB 3: MY PROFILE
    # ==========================================
    with tab_profile:
        st.title("👤 My Profile")
        
        # Edit Profile Settings
        new_name = st.text_input("Name", st.session_state['user_profile']['name'])
        new_loc = st.text_input("Location", st.session_state['user_profile']['location'])
        
        # We need to find the index of the current language to set it as default in the selectbox
        lang_index = 0
        languages = ["English", "Español (Spanish)", "Français (French)", "हिन्दी (Hindi)", 
                     "العربية (Arabic)", "中文 (Mandarin)", "Português (Portuguese)", "Русский (Russian)", "Bhojpuri (भोजपुरी)"]
        if st.session_state['user_profile']['language'] in languages:
            lang_index = languages.index(st.session_state['user_profile']['language'])
            
        new_lang = st.selectbox("Update Preferred Language", languages, index=lang_index)
        
        if st.button("💾 Save Profile Changes"):
            st.session_state['user_profile']['name'] = new_name
            st.session_state['user_profile']['location'] = new_loc
            st.session_state['user_profile']['language'] = new_lang
            st.success("Profile Updated!")
            st.rerun()
            
        st.divider()
        st.subheader("Danger Zone")
        if st.button("🚪 Sign Out", type="primary"):
            st.session_state['logged_in'] = False
            st.rerun() 
