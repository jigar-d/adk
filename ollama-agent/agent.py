from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

ollama_model = LiteLlm(model="ollama_chat/llama3.1:8b")

root_agent = Agent(
    name="OllamaAgent",
    model=ollama_model,
    description="An agent that uses the Ollama LLM for various tasks.",
    instruction="You are a helpful assistant powered by the Ollama LLM.",
    tools=[],
)