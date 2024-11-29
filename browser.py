from asyncio import run
from browser_use import Agent
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

llm = ChatOllama(
    model="llama3-groq-tool-use:8b",
    base_url="http://localhost:11434",
)

agent = Agent(
    task="Go to google.com and search for 'Albert Einstein'.",
    llm=llm,
)

run(agent.run())