import streamlit as st
import uuid
from backend import Chatbot, sqlite3, AIMessage, HumanMessage

def generate_thread_id():
    id = str(uuid.uuid4())
    return id

def load_chat(thread_id: str):
    res = Chatbot.get_state({"configurable": {"thread_id": thread_id}})
    if res.values:
        return res.values["messages"]
    else:
        return []

def load_threads():
    threads = st.session_state["chat_threads"]
    return threads

def start_new():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = []
    st.session_state["chat_threads"].append(thread_id)
    st.session_state["message_history"] = []

def load_saved_threads():
    conn = sqlite3.connect('lang_tools.db', check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY checkpoint_id DESC"
        )
        threads = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        threads = []
    finally:
        conn.close()
    return threads

if "chat_threads" not in st.session_state:
    threads = load_saved_threads()
    st.session_state["chat_threads"] = threads

if "thread_id" not in st.session_state:
    if st.session_state["chat_threads"]:
        st.session_state["thread_id"] = st.session_state["chat_threads"][0]
    else:
        thread_id = generate_thread_id()
        st.session_state["thread_id"] = thread_id
        st.session_state["chat_threads"].append(thread_id)

if "message_history" not in st.session_state:
    st.session_state["message_history"] = load_chat(st.session_state["thread_id"])

st.sidebar.title("Langbot")

if st.sidebar.button("New Chat"):
    start_new()
st.sidebar.header("Conversations")

for thread in st.session_state["chat_threads"]:
    if st.sidebar.button(str(thread)):
        print(thread)
        messages = load_chat(thread)
        st.session_state["thread_id"] = thread
        st.session_state["message_history"] = messages

for message in st.session_state["message_history"]:
    role = 'assistant' if isinstance(message, AIMessage) else "user"
    with st.chat_message(role):
        st.markdown(str(message.content))
input_text = st.chat_input("Ask me anything...")

if input_text:
    st.session_state["message_history"].append(HumanMessage(content=input_text))
    with st.chat_message("user"):
        st.markdown(input_text)
    conversation = st.session_state["message_history"]
    thread_id = st.session_state["thread_id"]
    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "metadata": {
            "thread_id": thread_id
        },
        "run_name": "talk_to_llm"
    }
    payload = {
        "messages": conversation
    }
    def ai_message_only():
        for message_chunk, metadata in Chatbot.stream(payload, config=config, stream_mode="messages"):
            if isinstance(message_chunk, AIMessage):
                yield message_chunk.content
    response = st.write_stream(ai_message_only())
    st.session_state["message_history"].append(AIMessage(content=response))




