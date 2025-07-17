from google.adk.tools import BaseTool

class ManualFormatterTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="manual_formatting",
            description="Applies basic markdown structure to PDLC text."
        )
    def run(self, input_data: dict) -> str:
        text = input_data.get("input", "")
        return f"# PDLC Document\n\n{text.strip()}"