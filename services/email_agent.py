import os
import glob
import smtplib
from typing import TypedDict, Annotated, List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import dotenv

# Load environment variables
dotenv.load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# Mock Email Database
LOB_EMAILS = {
    "AUTO": "madhumadhu112120052@gmail.com",
    "PROPERTY": "madhumadhu112120052@gmail.com",
    "GL": "madhumadhu112120052@gmail.com",
    "WC": "madhumadhu112120052@gmail.com",
    "UNKNOWN": "madhumadhu112120052@gmail.com"
}

# Base directory for claims data
# Assumes structure: ./lob/{LOB_NAME}/{POLICY_NUMBER}/*.pdf
BASE_DATA_DIR = "lob"

# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    user_query: str
    policy_number: Optional[str]
    lob: Optional[str]
    file_path: Optional[str]
    email_sent: bool
    error: Optional[str]
    logs: List[str]

# ============================================================================
# Models
# ============================================================================

class ExtractionResult(BaseModel):
    policy_number: str = Field(description="The policy number or claim number extracted from the text")
    lob: str = Field(description="The Line of Business (AUTO, PROPERTY, GL, WC). Map 'vehicle' to AUTO.")

# ============================================================================
# Nodes
# ============================================================================

def extract_info_node(state: AgentState):
    """
    Extracts Policy Number and LoB from the user query using Gemini.
    """
    print("--- Extracting Info ---")
    query = state['user_query']
    
    # Initialize LLM
    # Ensure GOOGLE_API_KEY is set in environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        return {
            "error": "GOOGLE_API_KEY not found in environment variables.",
            "logs": state['logs'] + ["Error: Missing GOOGLE_API_KEY"]
        }

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    parser = JsonOutputParser(pydantic_object=ExtractionResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert insurance assistant. Extract the Policy Number and Line of Business (LoB) from the user's request.\n"
                   "Valid LoBs are: AUTO, PROPERTY, GL, WC.\n"
                   "If the user mentions 'vehicle', 'car', 'accident', map it to AUTO.\n"
                   "If the user mentions 'house', 'home', 'fire', map it to PROPERTY.\n"
                   "Return JSON only.\n\n{format_instructions}"),
        ("user", "{query}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({"query": query, "format_instructions": parser.get_format_instructions()})
        print(f"Extracted: {result}")
        return {
            "policy_number": result.get("policy_number"),
            "lob": result.get("lob").upper(),
            "logs": state['logs'] + [f"Extracted Policy: {result.get('policy_number')}, LoB: {result.get('lob')}"]
        }
    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}",
            "logs": state['logs'] + [f"Extraction Error: {str(e)}"]
        }

def locate_document_node(state: AgentState):
    """
    Searches for the PDF file in the local file system.
    """
    print("--- Locating Document ---")
    if state.get("error"):
        return state

    policy_number = state['policy_number']
    lob = state['lob']
    
    # Construct search pattern
    # Pattern: lob/{LOB}/{POLICY_NUMBER}/*.pdf
    # We'll try a few variations to be robust
    
    search_patterns = [
        os.path.join(BASE_DATA_DIR, lob, policy_number, "*.pdf"),
        os.path.join(BASE_DATA_DIR, "*", policy_number, "*.pdf"), # Ignore LoB folder if needed
        os.path.join(BASE_DATA_DIR, "**", f"*{policy_number}*.pdf"), # Recursive search for filename
    ]
    
    found_file = None
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        if files:
            found_file = files[0] # Take the first match
            break
    
    if found_file:
        print(f"Found file: {found_file}")
        return {
            "file_path": found_file,
            "logs": state['logs'] + [f"Found file at: {found_file}"]
        }
    else:
        return {
            "error": f"No PDF found for Policy {policy_number} in LoB {lob}",
            "logs": state['logs'] + ["File not found"]
        }

def send_email_node(state: AgentState):
    """
    Sends an email with the attachment using SMTP.
    """
    print("--- Sending Email ---")
    if state.get("error"):
        return state

    lob = state['lob']
    file_path = state['file_path']
    recipient = LOB_EMAILS.get(lob, LOB_EMAILS["UNKNOWN"])
    
    subject = f"Claims Document for Policy {state['policy_number']} ({lob})"
    body = f"Please find attached the claims document for Policy {state['policy_number']}."
    
    # SMTP Configuration
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_username or not smtp_password:
        return {
            "error": "SMTP credentials not found in environment variables.",
            "logs": state['logs'] + ["Error: Missing SMTP credentials"]
        }

    print(f"📧 SENDING EMAIL...")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Attachment: {file_path}")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with open(file_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)
        
        # Connect to SMTP Server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        print("✅ Email sent successfully")
        
        return {
            "email_sent": True,
            "logs": state['logs'] + [f"Email sent to {recipient}"]
        }
    except Exception as e:
        return {
            "error": f"Failed to send email: {str(e)}",
            "logs": state['logs'] + [f"Email Error: {str(e)}"]
        }

# ============================================================================
# Graph Construction
# ============================================================================

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("extract_info", extract_info_node)
    workflow.add_node("locate_document", locate_document_node)
    workflow.add_node("send_email", send_email_node)
    
    workflow.set_entry_point("extract_info")
    
    workflow.add_edge("extract_info", "locate_document")
    workflow.add_edge("locate_document", "send_email")
    workflow.add_edge("send_email", END)
    
    return workflow.compile()

# ============================================================================
# Helper: Create Dummy Data
# ============================================================================

def create_dummy_data():
    """Creates a dummy folder structure and PDF for testing."""
    import fpdf
    
    # Structure: lob/AUTO/2456/claim_doc.pdf
    path = os.path.join(BASE_DATA_DIR, "AUTO", "2456")
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "12chhcy.pdf")
    if not os.path.exists(file_path):
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Dummy Claims Document for Policy 2456", ln=1, align="C")
        pdf.output(file_path)
        print(f"Created dummy file at: {file_path}")

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    # Create dummy data for the user to test immediately
    try:
        import fpdf
        create_dummy_data()
    except ImportError:
        print("Install fpdf to generate dummy data: pip install fpdf")
        # Create empty file if fpdf missing
        path = os.path.join(BASE_DATA_DIR, "AUTO", "2456")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "12chhcy.pdf"), "w") as f:
            f.write("Dummy PDF content")

    # Initialize Graph
    app = build_graph()
    
    # Example User Query
    user_input = "I have a claim for policy 2456 regarding a vehicle accident."
    print(f"\n🤖 User Query: '{user_input}'\n")
    
    initial_state = {
        "user_query": user_input,
        "policy_number": None,
        "lob": None,
        "file_path": None,
        "email_sent": False,
        "error": None,
        "logs": []
    }
    
    # Run the graph
    result = app.invoke(initial_state)
    
    print("\n--- Final State ---")
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Workflow Completed Successfully")
        print(f"Logs: {result['logs']}")
