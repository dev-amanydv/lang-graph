import streamlit as st
import uuid
from langgraph_backend import chatbot, AIMessage, HumanMessage, SystemMessage, sqlite3

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id

def start_new():
    thread_id = generate_thread_id()
    st.session_state['chat_threads'].append(thread_id)
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = []

def load_chat(thread_id):
    states = chatbot.get_state({"configurable": {"thread_id": thread_id}})
    if states.values:
        return states.values["messages"]
    else:
        return []

def load_threads():
    threads = st.session_state["chat_threads"]
    return threads

def get_saved_threads():
    conn = sqlite3.connect("chatbot.db", check_same_thread=False)
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
    loaded_threads = get_saved_threads()
    st.session_state["chat_threads"] = loaded_threads

if "thread_id" not in st.session_state:
    if st.session_state["chat_threads"]:
        st.session_state["thread_id"] = st.session_state["chat_threads"][0]
    else:
        thread_id = generate_thread_id()
        st.session_state["thread_id"] = thread_id
        st.session_state["chat_threads"].append(thread_id)

if "message_history" not in st.session_state:
    st.session_state["message_history"] = load_chat(st.session_state["thread_id"])

st.sidebar.title("LangBot")
if st.sidebar.button("New Chat"):
    start_new()
st.sidebar.header("Conversations")
for thread in st.session_state['chat_threads']:
    print(thread)
    if st.sidebar.button(str(thread)):
        messages = load_chat(thread)
        print("THREAD_ID: ", thread, " MESSAGES: ", messages)
        st.session_state["message_history"] = messages
        st.session_state["thread_id"] = thread

for message in st.session_state["message_history"]:
    role = "assistant" if isinstance(message, AIMessage) else "user"
    with st.chat_message(role):
        st.markdown(str(message.content))

user_input = st.chat_input("Ask something...")
if user_input:
    st.session_state["message_history"].append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.markdown(str(user_input))
    chat_messages = st.session_state["message_history"]
    thread_id = st.session_state["thread_id"]
    config = {"configurable": {"thread_id": thread_id},
              "metadata": {
                  "thread_id": thread_id
              },
              "run_name": "talk_to_llm"}
    input_payload = {"messages": [HumanMessage(content=user_input)]}
    response = st.write_stream(message_chunk.content for message_chunk, metadata in chatbot.stream(input_payload, config=config, stream_mode="messages"))
    print("response: ", response)
    st.session_state["message_history"].append(AIMessage(content=response))
