"""
Test Script for Transcript Analysis LangGraph Workflow
Demonstrates the 6-step analysis pipeline for call transcript quality assessment.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcript_analysis_graph import TranscriptAnalysisService


def create_sample_data() -> pd.DataFrame:
    """Create sample transcript data for testing"""
    
    sample_transcripts = [
        {
            "Transcript_ID": "T001",
            "Agent_ID": "A101",
            "Agent_Name": "John Smith",
            "Transcript_Call": """
Agent: Hi, this is John from customer service. How can I help you?
Customer: I need to file a claim. I was in a car accident yesterday.
Agent: Okay, let me help you with that. Can you tell me what happened?
Customer: I was rear-ended at a stop light. The other driver was texting.
Agent: I'm sorry to hear that. Let me get your information. What's your name?
Customer: Michael Johnson.
Agent: And your phone number?
Customer: 555-1234.
Agent: Alright. Where did this happen?
Customer: On Main Street, near the grocery store.
Agent: Got it. Was anyone injured?
Customer: No, everyone is fine.
Agent: Good. I'll create a claim for you. Your claim number is CLM-12345.
Customer: Thank you.
Agent: Anything else I can help with?
Customer: No, that's all.
Agent: Have a good day.
            """
        },
        {
            "Transcript_ID": "T002",
            "Agent_ID": "A102",
            "Agent_Name": "Sarah Davis",
            "Transcript_Call": """
Agent: Hello, thank you for calling. This is Sarah. I need to inform you this call may be recorded for quality purposes. How may I assist you today?
Customer: Hi, I need to report an accident.
Agent: I'm so sorry to hear that. Before we proceed, are you in a safe location? Does anyone need immediate medical assistance?
Customer: Yes, we're all safe. No injuries.
Agent: That's good to hear. Let me verify your policy first. May I have your policy number?
Customer: It's POL-789456.
Agent: Thank you, Mr. Thompson. I'm verifying your policy now. Can you confirm your date of birth for security?
Customer: March 15, 1985.
Agent: Perfect. Now, can you tell me about the incident? When did it occur?
Customer: Yesterday around 3 PM.
Agent: And where exactly did this happen?
Customer: At the intersection of Oak Avenue and 5th Street, near the downtown area.
Agent: Were there any witnesses?
Customer: Yes, there was a woman who saw everything. She gave me her contact info.
Agent: That's helpful. Can you describe what happened?
Customer: Another car ran a red light and hit my passenger side.
Agent: Was there a police report filed?
Customer: Yes, report number 2024-5678.
Agent: Let me note that. Was your vehicle towed or is it drivable?
Customer: It was towed. It's not drivable.
Agent: I understand. Do you need a rental car?
Customer: Yes, that would be great.
Agent: I'll arrange that for you. Your claim number is CLM-67890. An adjuster will contact you within 24 hours. Is your phone number 555-9876 still the best way to reach you?
Customer: Yes, that's correct.
Agent: And your email is still thompson@email.com?
Customer: Yes.
Agent: Perfect. Is there anything else I can help you with today?
Customer: No, thank you for all your help.
Agent: You're welcome. Take care and we'll be in touch soon.
            """
        },
        {
            "Transcript_ID": "T003",
            "Agent_ID": "A103",
            "Agent_Name": "Mike Wilson",
            "Transcript_Call": """
Agent: Yeah, hello?
Customer: Um, I need to report a claim.
Agent: What happened?
Customer: My car was damaged in a hail storm.
Agent: When?
Customer: Last Tuesday.
Agent: [long pause] Okay, hold on... [typing sounds for 30 seconds]
Customer: Hello?
Agent: Yeah, I'm here. What's your name?
Customer: Jennifer Brown.
Agent: Policy number?
Customer: I don't have it with me.
Agent: [sighs] Can you look it up?
Customer: I'm not at home right now.
Agent: Fine. What's your social?
Customer: 123-45-6789.
Agent: Alright, I found you. So hail damage?
Customer: Yes, the roof is dented and the windshield has cracks.
Agent: You'll need to get it inspected. Take it somewhere.
Customer: Where should I take it?
Agent: Any body shop, I guess. They'll give you an estimate.
Customer: Okay... what's my claim number?
Agent: CLM-11111. Bye.
Customer: Wait, I have more questions...
[Call disconnected]
            """
        }
    ]
    
    return pd.DataFrame(sample_transcripts)


def main():
    """Main test function"""
    print("=" * 60)
    print("TRANSCRIPT ANALYSIS LANGGRAPH WORKFLOW TEST")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        return
    
    print("\n✅ API key found")
    
    # Create sample data
    print("\n📝 Creating sample transcript data...")
    df = create_sample_data()
    print(f"   Created {len(df)} sample transcripts")
    
    # Initialize service
    print("\n🔧 Initializing TranscriptAnalysisService...")
    try:
        service = TranscriptAnalysisService()
        print("   Service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize service: {e}")
        return
    
    # Run analysis
    print("\n🚀 Starting transcript analysis workflow...")
    print("   This will execute the following steps:")
    print("   1. Initialize workflow")
    print("   2. Identify mistakes in each transcript")
    print("   3. Aggregate all mistakes")
    print("   4. Generate 10 common mistake themes")
    print("   5. Map mistakes to themes for each transcript")
    print("   6. Analyze root causes")
    print("   7. Calculate severity scores")
    print("   8. Generate detailed reasoning")
    print("   9. Compile final results")
    print("\n   Please wait, this may take several minutes...\n")
    
    try:
        result = service.analyze(df)
        
        if result.get("success"):
            print("\n" + "=" * 60)
            print("✅ ANALYSIS COMPLETE!")
            print("=" * 60)
            
            # Display summary
            summary = result.get("summary", {})
            print(f"\n📊 SUMMARY:")
            print(f"   Transcripts Analyzed: {summary.get('total_transcripts_analyzed', 0)}")
            print(f"   Total Mistakes Found: {summary.get('total_mistakes_identified', 0)}")
            print(f"   Avg Mistakes/Transcript: {summary.get('average_mistakes_per_transcript', 0):.1f}")
            print(f"   Avg Severity Score: {summary.get('average_severity_score', 0):.1f}/100")
            print(f"   Themes Generated: {summary.get('themes_generated', 0)}")
            
            # Display generated themes
            themes = result.get("generated_themes", [])
            print(f"\n🎯 GENERATED MISTAKE THEMES ({len(themes)}):")
            for theme in themes:
                print(f"   {theme.get('theme_number', '?')}. {theme.get('theme_name', 'Unknown')}")
                print(f"      Definition: {theme.get('definition', '')[:80]}...")
            
            # Display per-transcript results
            final_results = result.get("final_results", [])
            print(f"\n📝 INDIVIDUAL TRANSCRIPT RESULTS:")
            for res in final_results:
                print(f"\n   {'─' * 50}")
                print(f"   Transcript: {res.get('transcript_id')}")
                print(f"   Agent: {res.get('agent_name')} ({res.get('agent_id')})")
                print(f"   Mistakes Found: {res.get('mistakes_count', 0)}")
                print(f"   Severity Score: {res.get('severity_score', 100)}/100 ({res.get('severity_rating', 'N/A')})")
                
                themes_present = res.get("mistake_themes", [])
                if themes_present:
                    print(f"   Themes: {', '.join(themes_present[:3])}")
                
                root_causes = res.get("primary_root_causes", [])
                if root_causes:
                    print(f"   Root Causes: {', '.join(root_causes[:2])}")
            
            # Export to DataFrame
            print(f"\n💾 EXPORTING RESULTS...")
            results_df = service.get_results_dataframe(result)
            output_file = "transcript_analysis_results.csv"
            results_df.to_csv(output_file, index=False)
            print(f"   Results exported to: {output_file}")
            
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
