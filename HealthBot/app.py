import streamlit as st
import requests
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Health Assistant", page_icon="🏥", layout="wide")

# --- SIDEBAR: SETUP ---
# check if key is in secrets (cloud), Otherwise ask user (Local)
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.sidebar.header("⚙️ Settings")
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")
st.sidebar.markdown("[Get a Free Key Here](https://console.groq.com/keys)")
st.sidebar.info("💡 Tip: This bot checks official US data first. If not found (e.g., Indian brands), it uses AI knowledge.")

# --- FUNCTION 1: THE PHARMACIST (Official Data) ---
def get_fda_drug_info(drug_name):
    """Fetches real drug label data from OpenFDA (US Database)"""
    base_url = "https://api.fda.gov/drug/label.json"
    query = f'?search=openfda.brand_name:"{drug_name}"&limit=1'
    
    try:
        response = requests.get(base_url + query)
        data = response.json()
        
        if "error" in data:
            return None
            
        result = data['results'][0]
        return {
            "source": "Official US FDA Database",
            "purpose": result.get('purpose', ['Not Listed'])[0],
            "indications": result.get('indications_and_usage', ['Not Listed'])[0],
            "warnings": result.get('warnings', ['Not Listed'])[0][:1000] 
        }
    except:
        return None

# --- FUNCTION 2: THE INTELLIGENT BRAIN (AI Logic) ---
def get_ai_response(user_query, context_data=None, mode="symptom"):
    if not api_key:
        return "Please enter your API Key in the sidebar first!"
    
    # Use Llama 3.3 (Smartest Free Model)
    llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")

    # LOGIC BRANCHING
    if mode == "drug_with_context":
        # We have official FDA data
        system_text = "You are a helpful pharmacist. Explain this technical medical data in simple English for a patient."
        input_text = f"Official Data: {str(context_data)}\n\nUser Question: {user_query}"
        
    elif mode == "drug_no_context":
        # FDA failed (Likely Indian/Local Brand), rely on AI Memory
        system_text = """
        You are an expert pharmacist familiar with international medicines, including Indian brands (like Dolo, Saridon, Pan D).
        1. Identify the active ingredients in the drug name provided.
        2. Explain its uses and side effects.
        3. Provide a warning: "Information based on general knowledge, check the strip pack."
        """
        input_text = f"Explain the medicine: {user_query}"
        
    else:
        # Symptom Checker
        system_text = """
        You are a senior medical triage nurse.
        1. Ask follow-up questions if the user's description is too vague.
        2. Identify if this is an emergency (Heart attack, Stroke, Anaphylaxis).
        3. Suggest specialist doctors (e.g., 'See a Gastroenterologist').
        4. Suggest supportive home care (hydration, rest).
        5. DISCLAIMER: Always state you are an AI, not a doctor.
        """
        input_text = user_query

    # Create Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_instruction}"),
        ("human", "{user_input}"),
    ])

    # Execute
    chain = prompt | llm
    response = chain.invoke({
        "system_instruction": system_text,
        "user_input": input_text
    })
    
    return response.content

# --- MAIN PAGE UI ---
st.title("🏥 Global Health Companion")
st.markdown("### 🇮🇳 India-Ready | 🚑 Emergency Support | 💊 Drug Info")

# Create 3 Tabs
tab1, tab2, tab3 = st.tabs(["🤒 Symptom Checker", "💊 Medicine Info", "🚑 Emergency Help"])

# --- TAB 1: SYMPTOM CHECKER ---
with tab1:
    st.write("Describe your problem. Include Age and Duration.")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=25)
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
    symptoms = st.text_area("Symptoms (e.g., 'High fever, shivering, joint pain since yesterday')")
    
    if st.button("Analyze Symptoms"):
        if symptoms:
            full_query = f"Age: {age}, Gender: {gender}, Symptoms: {symptoms}"
            with st.spinner("Consulting medical guidelines..."):
                response = get_ai_response(full_query, mode="symptom")
                st.markdown(response)
        else:
            st.warning("Please enter symptoms.")

# --- TAB 2: MEDICINE INFO (UPDATED FOR INDIAN DRUGS) ---
with tab2:
    st.write("Enter any medicine name (US Brand or Indian Brand)")
    drug_name = st.text_input("Medicine Name (e.g., 'Dolo 650', 'Advil', 'Pan 40')")
    
    if st.button("Get Medicine Details"):
        if drug_name:
            with st.spinner(f"Searching information for {drug_name}..."):
                # Step 1: Try Official US Database
                real_data = get_fda_drug_info(drug_name)
                
                if real_data:
                    st.success(f"✅ Found in Official FDA Database")
                    explanation = get_ai_response(f"Explain {drug_name}", context_data=real_data, mode="drug_with_context")
                    st.write(explanation)
                    with st.expander("View Technical Data"):
                        st.json(real_data)
                else:
                    # Step 2: Fallback to AI Knowledge (For Indian/Local drugs)
                    st.info(f"⚠️ Not in US Database. Searching AI Knowledge Base (Good for Indian Brands)...")
                    explanation = get_ai_response(drug_name, mode="drug_no_context")
                    st.write(explanation)

# --- TAB 3: EMERGENCY HELP (NEW) ---
with tab3:
    st.error("🚨 IN CASE OF EMERGENCY")
    st.write("If the patient is unconscious, bleeding heavily, or having chest pain, DO NOT USE THIS BOT.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📞 Emergency Numbers (India)")
        st.markdown("- **Ambulance:** 102 / 108")
        st.markdown("- **Police:** 100 / 112")
        st.markdown("- **Women Helpline:** 1091")
        
    with col2:
        st.markdown("### 🏥 Find Help Nearby")
        user_city = st.text_input("Enter your City Name (e.g., Mumbai, Bangalore):")
        
        if user_city:
            # Generate dynamic Google Maps Links
            hospital_link = f"https://www.google.com/maps/search/hospitals+near+{user_city}"
            ambulance_link = f"https://www.google.com/maps/search/ambulance+service+near+{user_city}"
            
            st.markdown(f"👉 **[Click to Find Hospitals in {user_city}]({hospital_link})**")

            st.markdown(f"👉 **[Click to Find Ambulance Services in {user_city}]({ambulance_link})**")

