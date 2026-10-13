from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from typing import TypedDict, Annotated
from pydantic import BaseModel
import os
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3
from langchain_core.tools import tool
from ddgs import DDGS
import requests
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")

model = ChatOpenAI(
    model="openai/gpt-oss-120b",
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key,
)

@tool
def search_tool(query: str) -> str:
    """
    Search the web with DuckDuckGo and return the top results.
    """
    results = DDGS().text(query, max_results=5)
    print("EXECUTED DUCk DUCK GO SEARCH")
    print(results)
    return "\n\n".join(f"{r['title']}\n{r['body']}\n{r['href']}" for r in results)

@tool
def calculator(first_num: float, second_num: float, operation: str)-> dict:
    """
    Perform a basic arithematic operation on two numbers.
    Supported operations: add, sub, multiply and divide
    """
    print(f"EXECUTED CALCULATOR")
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "multiply":
            result = first_num * second_num
        elif operation == "divide":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": "Unsupported operation"}
        print("==============")
        print(f"Result: ", result)
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for the given symbol(eg. 'AAPL', 'TSLA')
    using Alpha Vantage with api key in url
    """
    APLHA_VENTAGE_API_KEY="7R1KOR2MJ67EQAEM"
    url = (
        f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={APLHA_VENTAGE_API_KEY}"
    )
    r = requests.get(url)
    return r.json()

tools = [search_tool, get_stock_price, calculator]
llm_with_tools = model.bind_tools(tools=tools)


class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

conn = sqlite3.connect(database="lang_tools.db", check_same_thread=False)
checkpointer=SqliteSaver(conn=conn)
checkpointer.setup()

def chat_node(state: ChatbotState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {
        "messages": [response]
    }

tool_node = ToolNode(tools)

graph = StateGraph(ChatbotState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat_node")

graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

Chatbot = graph.compile(checkpointer=checkpointer)

# Helper function

def retrive_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)
