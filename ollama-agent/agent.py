from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext
import os
import io
import pdfplumber

from pypdf import PdfReader

class PdfReaderError(Exception):
    pass


async def check_uploaded_document(tool_context: ToolContext) -> str:
    """
    Checks if the specified document is uploaded and available in the session state.
    Args:
        tool_context: The context object provided by the ADK framework, containing state.
    Returns:
        A confirmation message.
    """
    # Check if the document is uploaded by looking for it in the session state

    print("------------------------------------------------")
    artifact_ids = await tool_context.list_artifacts()

    # Get the first artifact ID from the list which is the doc uploaded by the user
    artifact_id = artifact_ids[0]
    print(f"Reading artifact with ID: {artifact_id}")


    # 2. Read the content of the artifact
    # Await the coroutine to get the data
    try:
        artifact_content = await tool_context.load_artifact(artifact_id)
        print( "The doc type: ", artifact_content.inline_data.mime_type )
        file_name = artifact_content.inline_data.display_name
        pdf_bytes = artifact_content.inline_data.data
        pdf_bytes_stream = io.BytesIO(pdf_bytes) 
    except FileNotFoundError:
        print(f"Error: Artifact '{file_name}' not found.")


    try:
        # Test to check if the uploaded doc is a pdf:
        # Attempt to initialize a PdfReader. This will try to parse the PDF structure.
        # It's a robust check that will fail on corrupted or malicious files.
        reader = PdfReader(pdf_bytes_stream)

        # A simple sanity check. If the file has no pages, it's not a valid PDF.
        if not reader.pages:
            raise PdfReaderError("PDF contains no pages.")
    except Exception as e:
        # Wrap the original exception in a more informative error.
        raise PdfReaderError(f"Failed to parse PDF securely: {e}") from e

    try:   
        # Use io.BytesIO to treat the bytes as a file-like object
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                # Extract the text from each page and append it
                full_text += page.extract_text() + "\n"

        print("Successfully extracted text from the PDF.")
        print("\n--- Extracted Text ---")
        print("The number of characters extractd in full-text: ", len( full_text ))
        

    except Exception as e:
        print(f"An error occurred: {e}")
    print("------------------------------------------------")

    return "Document uploaded successfully"

ollama_model = LiteLlm(model="ollama_chat/gemma3:1b")

root_agent = Agent(
    name="OllamaAgent",
    model=ollama_model,
    description="An agent that uses the Ollama LLM for various tasks.",
    instruction="You are a helpful assistant powered by the Ollama LLM. If user uploads a document, confirm the upload. Else respond normally.",
    tools=[FunctionTool(check_uploaded_document)
],
)
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="OllamaApp",
    session_service=session_service,
    artifact_service=artifact_service
)