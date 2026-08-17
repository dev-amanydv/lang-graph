from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, List


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
checkpoint = InMemorySaver()
def chat_node(state: ChatbotState):
    messages = state['messages']
    print("**************************")
    print(messages)
    print("**************************")
    response = model.invoke(messages).content
    return {
        'messages': [response]
    }

graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpoint)

def main():
    initial_state = {
        "messages": [
            SystemMessage(
                content="You have to give answers to user queries in arrogant and insulting manner"
            )
        ]
    }

    while True:
        user_input = input("Ask me anything...")
        print("User: ", user_input)
        if user_input.strip().lower() in ["bye", "quit", "exit"]:
            break
        config = {"configurable": {"thread_id": "thread-1"}}
        response = chatbot.invoke(
            {**initial_state, "messages": [HumanMessage(content=user_input)]}, config=config
        )
        print("AI: ", response["messages"][-1].content)

if __name__ == '__main__':
    main()
