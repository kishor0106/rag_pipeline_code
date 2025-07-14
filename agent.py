import vertexai
from google.adk.agents import LlmAgent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag
import os
from dotenv import load_dotenv
from .instruction import multi_domain_compliance_instructions

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# === Financial Services Compliance Tool ===
financial_tool = VertexAiRagRetrieval(
    name='financial_services_compliance',
    description='Retrieve and analyze financial services compliance materials, including banking regulations, credit card policies, electronic transfers, and payment systems.',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/5685794529555251200")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.75
)

# === Insurance Compliance Tool ===
insurance_tool = VertexAiRagRetrieval(
    name='insurance_compliance',
    description='Search insurance domain compliance content such as IRDAI guidelines, claim procedures, policy disclosures, and underwriting regulations.',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/2227030015734710272")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.75
)

# === General Compliance Tool ===
general_tool = VertexAiRagRetrieval(
    name='general_compliance',
    description='Analyze general compliance documentation that is not specific to the financial or insurance verticals (e.g., data retention, audit procedures, corporate policies).',
    rag_resources=[
        rag.RagResource(rag_corpus=f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/3746994889972252672")
    ],
    similarity_top_k=5,
    vector_distance_threshold=0.75
)

# === Agent with static tools ===
root_agent = LlmAgent(
    name='multi_domain_compliance_agent',
    model='gemini-2.0-flash',
    description='Routes compliance queries to the appropriate financial services, insurance, or general tool with citation-enhanced responses.',
    instruction=multi_domain_compliance_instructions,
    tools=[
        financial_tool,
        insurance_tool,
        general_tool
    ]
)

print(" Multi-domain Compliance Agent initialized successfully with vertical-based tools.")



