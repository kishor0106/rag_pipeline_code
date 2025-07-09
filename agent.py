import vertexai
from google.adk.agents import LlmAgent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag
import os
from dotenv import load_dotenv
from instruction import multi_domain_compliance_instructions

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# === Tools for Specified Domains ===
credit_card_tool = VertexAiRagRetrieval(
    name='credit_card_compliance',
    description='Search credit card compliance documents',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/1152921504606846976")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.6
)

federal_deposit_tool = VertexAiRagRetrieval(
    name='federal_deposit_compliance',
    description='Search federal deposit compliance documents',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/2882303761517117440")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.6
)

electronic_fund_tool = VertexAiRagRetrieval(
    name='electronic_fund_transfer_compliance',
    description='Search electronic fund transfer compliance documents',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/8070450532247928832")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.6
)

general_tool = VertexAiRagRetrieval(
    name='general_compliance',
    description='Search general compliance documents not tied to a specific domain',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/3596124302455341056")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.6
)

# === Agent with Static Tools ===
root_agent = LlmAgent(
    name='multi_domain_compliance_agent',
    model='gemini-2.0-flash',
    description='Routes queries to the correct compliance domain tool',
    instruction=multi_domain_compliance_instructions,
    tools=[
        credit_card_tool,
        federal_deposit_tool,
        electronic_fund_tool,
        general_tool
    ]
)

print("Multi-domain Compliance Agent initialized successfully!")
