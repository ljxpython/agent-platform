from langchain_pymupdf4llm import PyMuPDF4LLMLoader

loader = PyMuPDF4LLMLoader(
    "/Users/bytedance/PycharmProjects/test/2025-11-01_graph_python/src/file_agent/滴滴出行行程报销单.pdf",
    mode="single",  # 作为单个文档处理
    table_strategy="lines",  # 提取表格
)
documents = loader.load()

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = text_splitter.split_text(documents[0].page_content)
print(texts)
print(len(texts))
# pragma: no cover  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002WVdZd1N3PT06NDJjMWMxMDg=
