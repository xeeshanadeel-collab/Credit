import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
import json # Used to parse the structured JSON output
import io

# --- 1. Configuration and Initialization ---

# WARNING: Replace this placeholder with your actual Gemini API Key.
# This method is INSECURE and should only be used for local testing.
GEMINI_API_KEY = "AIzaSyA0aVBVADHzgAN8-3hcf02VPh7sqnRa1FY"
MODEL = 'gemini-2.5-pro' # Model suitable for long-context and complex reasoning

# Initialize the Gemini Client
try:
    if GEMINI_API_KEY == "YOUR_HARDCODED_GEMINI_API_KEY_HERE" or not GEMINI_API_KEY:
        st.error("Please replace the placeholder value in the code with your actual GEMINI API Key.")
        st.stop()
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
except Exception as e:
    st.error(f"Error initializing Gemini Client: {e}")
    st.stop()


# --- 2. Compliance Logic Function ---

def get_compliance_analysis(document_1_file, policy_doc_file):
    """
    Sends the two documents and a detailed prompt to the Gemini API 
    for compliance analysis, requesting a structured JSON output.
    """
    st.info("Sending documents to Gemini for compliance analysis. This may take a moment...")
    
    # 1. Prepare files for the API (as Parts)
    try:
        doc1_part = types.Part.from_bytes(
            data=document_1_file.getvalue(),
            mime_type=document_1_file.type
        )
        policy_part = types.Part.from_bytes(
            data=policy_doc_file.getvalue(),
            mime_type=policy_doc_file.type
        )
    except Exception as e:
        st.error(f"Error reading file content: {e}")
        return None
    
    # 2. Construct the detailed prompt and system instructions
    system_prompt = (
        "You are an expert Credit Risk Analyst. Your task is to evaluate a Credit Document "
        "(Document 1) against a strict Credit Policy (Document 2). "
        "The goal is to determine if Document 1 is FULLY COMPLIANT with ALL requirements "
        "of Document 2. "
        "Your final output MUST be a single, valid JSON object with two top-level keys: 'compliance_status' "
        "and 'detailed_report'. The 'detailed_report' value MUST be a Markdown string. Do not include any other text outside the JSON."
    )
    
    user_prompt = (
        "Analyze Document 1 (the Credit Document) against Document 2 (the Policy). "
        "1. **COMPLIANCE STATUS**: Determine the overall compliance. Return 'COMPLIANT' or 'NON-COMPLIANT'."
        "2. **DETAILED REPORT**: Provide a structured breakdown in Markdown."
        "   - **SUMMARY**: A one-paragraph summary of your final finding."
        "   - **NON-COMPLIANT FINDINGS**: A bulleted list of *specific* policy sections (from Document 2) "
        "     that Document 1 violates, along with the exact reason for the violation."
        "   - **COMPLIANT AREAS**: A bulleted list of key areas (e.g., Collateral requirements, Debt-to-Income, etc.) "
        "     where Document 1 is explicitly compliant with the policy."
        "   - **MITIGATION/NEXT STEPS**: Suggest 1-2 concrete, professional next steps for remediation if non-compliant."
    )

    # 3. Configure the API call for JSON output
    contents = [doc1_part, policy_part, user_prompt]
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        # Enforce JSON output format
        response_mime_type="application/json",
        response_schema={
            "type": "object", 
            "properties": {
                "compliance_status": {"type": "string", "description": "Overall status: COMPLIANT or NON-COMPLIANT."}, 
                "detailed_report": {"type": "string", "description": "The detailed report formatted in Markdown."}
            }
        },
        temperature=0.1 # Low temperature for factual, deterministic analysis
    )
    
    # 4. Call the Gemini API
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config
        )
        return response.text
    except APIError as e:
        st.error(f"Gemini API Error: {e}. Please check your API key and file sizes.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


# --- 3. Streamlit UI Layout ---

st.set_page_config(
    page_title="Credit Policy Compliance Checker 📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Credit Policy Compliance Checker 📑")
st.markdown("Uses **Gemini 2.5 Pro** to evaluate a **Credit Document** against a **Policy Document**.")

st.sidebar.header("Document Upload")
document_1 = st.sidebar.file_uploader(
    "Upload Document 1 (The Credit File/Application)",
    type=['pdf', 'txt', 'docx'],
    key="doc1_uploader"
)
policy_document = st.sidebar.file_uploader(
    "Upload Document 2 (The Credit Policy)",
    type=['pdf', 'txt', 'docx'],
    key="policy_uploader"
)

# --- 4. Main Application Logic ---

if document_1 and policy_document:
    if st.sidebar.button("Run Compliance Check", key="run_check"):
        with st.spinner("Analyzing documents..."):
            json_report_str = get_compliance_analysis(document_1, policy_document)
            
            if json_report_str:
                try:
                    # Parse the JSON output from Gemini
                    report_data = json.loads(json_report_str)
                    
                    status = report_data.get('compliance_status', 'N/A')
                    report_markdown = report_data.get('detailed_report', 'No detailed report found.')

                    st.divider()

                    # Display the Compliance Status
                    if "COMPLIANT" in status.upper():
                        st.success(f"## ✅ Compliance Status: **{status}**")
                    elif "NON-COMPLIANT" in status.upper():
                        st.error(f"## ❌ Compliance Status: **{status}**")
                    else:
                        st.warning(f"## ⚠️ Compliance Status: **{status}**")
                    
                    st.markdown("---")
                    
                    # Display the Detailed Report using Markdown for structure
                    st.header("Detailed Compliance Report")
                    st.markdown(report_markdown)

                    st.markdown("---")
                    
                    # Optional: Display the raw data
                    with st.expander("View Raw JSON Output"):
                        st.json(report_data)

                except json.JSONDecodeError:
                    st.error("Error parsing the analysis from Gemini. The output was not a valid JSON object.")
                    st.text_area("Raw Gemini Output (for debugging):", json_report_str, height=200)
                except Exception as e:
                    st.error(f"An error occurred while processing the result: {e}")
            else:
                st.warning("Analysis failed. Please check the error messages above.")

else:
    st.info("Please upload both Document 1 (Credit Document) and Document 2 (Credit Policy) in the sidebar to begin the compliance check.")