import vertexai
from google.adk.agents import LlmAgent
from .instruction import pdlc_instruction
from .tool import ManualFormatterTool  
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

formatter_tool = ManualFormatterTool()

root_agent = LlmAgent(
    name="pdlc_document_ag",
    model="gemini-2.0-flash",
    description="You are an assistant that helps create clear and comprehensive documentation for software systems. Formats PDLC instructions into markdown-style documentation.",
    instruction=pdlc_instruction,
    tools=[formatter_tool]
)