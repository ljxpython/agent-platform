import asyncio

from file_rag.engines.file_chat_engine import FileChatEngineFactory

engine = asyncio.run(FileChatEngineFactory.create_engine())

graph = engine.graph
