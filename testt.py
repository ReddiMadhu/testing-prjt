import os
import pandas as pd
from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")  # Use environment variable instead of hardcoding
if not API_KEY:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable")

# --- Data Models ---
class SOPAudit(BaseModel):
    missed_elements: List[str] = Field(description="List of SOP elements that were missed in the transcript")

class State(TypedDict):
    transcript: str
    missed: List[str]

# --- LLM Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=API_KEY
)

structured_llm = llm.with_structured_output(SOPAudit)

# --- Prompts ---
parser = JsonOutputParser(pydantic_object=SOPAudit)

prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an FNOL call auditing agent. "
     "Identify which SOP elements were NOT followed based on the checklist provided. "
     "Return ONLY using the required JSON schema."
    ),
    ("human", 
     "Transcript:\n{transcript}\n\n"
     "SOP Checklist:\n{checklist}\n\n"
     "{format_instructions}"
    )
])

# --- Placeholder Data (You need to define these) ---
SOP_ELEMENTS = [
    "Verify Policy Number",
    "Ask for Date of Loss",
    "Confirm Driver Name",
    "Ask about Injuries"
]

# --- Graph Nodes ---
def evaluate_sop(state: State):
    transcript = state["transcript"]

    formatted_prompt = prompt.format(
        transcript=transcript,
        checklist="\n".join(SOP_ELEMENTS),
        format_instructions=parser.get_format_instructions()
    )

    # Invoke LLM
    try:
        llm_response = structured_llm.invoke(formatted_prompt)
        # Handle case where response might be None or malformed
        missed = llm_response.missed_elements if llm_response else []
    except Exception as e:
        print(f"Error invoking LLM: {e}")
        missed = []

    return {"missed": missed}

# --- Graph Construction ---
graph = StateGraph(State)
graph.add_node("evaluate_sop", evaluate_sop)
graph.add_edge(START, "evaluate_sop")
graph.add_edge("evaluate_sop", END)

workflow = graph.compile()

# --- Execution ---
if __name__ == "__main__":
    try:
        # Check if file exists
        if not os.path.exists("calls.xlsx"):
            raise FileNotFoundError("calls.xlsx not found in current directory")
        
        df = pd.read_excel("calls.xlsx")
        
        # Validate required column exists
        if "transcript" not in df.columns:
            raise KeyError("'transcript' column not found in calls.xlsx")
        
        results = []
        for idx, row in df.iterrows():
            print(f"Processing row {idx}...")
            output = workflow.invoke({"transcript": row["transcript"], "missed": []})
            results.append(output["missed"])
        
        # Output results
        df["missed_sop_elements"] = results
        df.to_excel("audit_results.xlsx", index=False)
        print(f"Processing complete. Results saved to audit_results.xlsx")
        print(f"Total rows processed: {len(results)}")
        
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except KeyError as e:
        print(f"Column error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")