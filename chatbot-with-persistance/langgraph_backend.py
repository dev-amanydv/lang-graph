from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import os
from langgraph.graph import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv
import sqlite3

load_dotenv(override=True)
hf_token = os.environ.get("HF_TOKEN")
hf_base_url = os.environ.get("HF_BASE_URL")

model = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V4-Flash-0731:novita",
    base_url=hf_base_url,
    api_key=hf_token,
)


class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


graph = StateGraph(ChatbotState)

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpoint = SqliteSaver(conn=conn)
checkpoint.setup()

def chat_node(state: ChatbotState):
    messages = state["messages"]
    print("User: ", messages)
    response = model.invoke(messages).content
    print("AI: ", response)

    return {"messages": [AIMessage(content=response)]}


graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpoint)


def main():
    user_input = input("Type something")
    initial_state = {
        "messages": [
            SystemMessage(
                content="Your name is Kally, and you are very extrovert and folksy. Always introduce yourself showing your folksy behaviour"
            )
        ]
    }
    config = {"configurable": {"thread_id": "thread-1"}}
    response = chatbot.invoke(
        {
            **initial_state,
            "messages": initial_state.get("messages", [])
            + [HumanMessage(content=user_input)],
        },
        config=config,
    )


if __name__ == "__main__":
    main()
