
prompt = f"""
You are an expert in FNOL call quality, insurance operation, agent coaching and training analysis.

Your task is to read the inputs I will provide and generate a set of tranining opportunities that can use to train the agents on their root causes across any FNOL call.

I give you:
1. A list of root cause and the reason of choosing that root causes..
2. The root cause list for which I want training opportunities.

Your Objective:
Using all inputs, generate a set of high-level, mutually exclusive and collectively exhaustive traning opportunities, that help agents so that they will not do any such mistakes again in the future.

The list I provide have the values like:
- [root cause 1 : reasoning 1, root cause 2 : reasoning 2,.....,so on]

Rules:
1. Read all the root causes and reasoning carefully and combine the meaning across all cases.
2. below is a root cause theme and its detailed reasoning. Based on this information, identify two types of training opportunities.
- Agent specific training: training focused on improving the individual agents skills, behaviour and communication or knowledge gaps
- Operational Process Training - training focused on improving workflow steps, process clarity, system usage, SOP adherance, cross team coordination.
3. Also provide a small summary about each training what should we provide in that training.
4. In the given list, I will provide repeating root cause with different explanation. so I want a specific training for each understading it using the reasoning.
6. Provide the output strictly in the following JSON format:

------------------------------------------------------------------
Root Cause list : [Attention & Active Listening Deficit,
Process Compliance Gap,
Probing Question Deficiency,
Verification & Confirmation Failure,
Hurrying through call without proper detail collection,
Language & Communication Barriers,
Documentation Accuracy Issues,
Assumption Based Decision Making,
Sequence & Context Understanding Gap,
Critical Detail Oversight
]

------------------------------------------------------------------
Root cause Themes : Reasoning List : {theme_reason}
------------------------------------------------------------------

The output should be in this JSON format only:
"""
def create_prompt(call_transcript, comments, error):
    prompt = f"""
You are an expert FNOL call analysis system designed to extract the exact root cause themes of quality issues from the given list of root cause themes.

I will provide:
1. The full FNOL Call Transcript.
2. The SPECIFIC ERROR Associated with this call given by the auditor.
3. The AUDITOR COMMENT describing the issue observed corresponding to that SPECIFIC ERROR.
4. The Defined list of ROOT CAUSE THEMES, which are the possible cause for the issue.

Your Task:
Your Objectvie:
Identify the most accurate and evidence based ROOT CAUSE THEME of the auditor observation. The root cause is basically answering why the auditor observed the issue. I already have the answer for what the issue by the auditor comments, but I want to answer why the issue happend from the given list.

Follow these rules:
1. Read the transcript CAREFULLY and identify the exact agent behaviour, action, inaction, misunderstanding, or process gap that caused the issue described by the auditor.

2. The root cause must:
- Be directly supported by the transcript
- Align with the auditor comment and the specific error.
- Describe the TRUE underlying reason for the mistake.
- Choose only from the given list of ROOT CAUSE THEMES.
- Do not fabricate any other root cause themes.

4. If the output, Do NOT include:
- Personal Information
- Agent Names
- Claimant Names
- Policy or Claim Number
- Any fabricated details
- Anything not explicitly supported by the transcript.

5. Output strictly in this JSON format as given below.

6. Reasoning rules:
- Only include short, relevant reason behind choosing that particular root cause themes among other available.
- Remove any personal identifiers.
- Do NOT fabricate anything, give me the precise reasoning.

7. Empathy Score:
- Provide an empathy score to the Agent, based on the call transcript.
- It should be from 0 to 100.
- The score should be based on the agent's empathetic response to the customer.

Your response must follow the format exactly and rely only on transcript evidence.

Root Cause Themes : [Attention & Active Listening Deficit,
Process Compliance Gap,
Probing Question Deficiency,
Verification & Confirmation Failure,
Hurrying through call without proper detail collection,
Language & Communication Barriers,
Documentation Accuracy Issues,
Assumption Based Decision Making,
Sequence & Context Understanding Gap,
Critical Detail Oversight
]

------------------------------------------------------------------
Auditors Comments : {comments}
Specific Error : {error}
------------------------------------------------------------------
Call Transcript : {call_transcript}
------------------------------------------------------------------

The output should be in this JSON format only:
```json
-------
{
  root_cause : Detailed root cause identified from transcript,
  reasoning : Reason of choosing that particular root cause theme among others.
  empathy_score : <0-100>
}
-------
Note : Don't give any free text in the output. No Notes.
"""
return prompt
