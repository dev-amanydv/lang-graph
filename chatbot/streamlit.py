import streamlit as st
from langgraph_backend import chatbot, HumanMessage
import uuid


def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def start_new():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['chat_threads'].append(thread_id)
    st.session_state['message_history'] = []

def load_chats(thread_id):
    state = chatbot.get_state({"configurable": {"thread_id": thread_id}})
    if state.values:
        return state.values['messages']
    return []


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

if 'thread_id' not in st.session_state:
    thread_id = generate_thread_id()
    print(thread_id)
    st.session_state['thread_id'] = thread_id
    st.session_state['chat_threads'].append(thread_id)

CONFIG = {"configurable": {"thread_id": st.session_state['thread_id']}}


st.sidebar.title('GraphBot')
if st.sidebar.button('New chat'):
    start_new()
st.sidebar.header('My Conversations')
for thread in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread)):
        st.session_state['thread_id'] = thread
        messages = load_chats(thread)
        temp_messages = []
        for msg in messages:
            print('isinstance ', isinstance(msg, HumanMessage))

            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here...')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    response = st.write_stream(message_chunk.content for message_chunk, metadata in chatbot.stream(
        {'messages': HumanMessage(content=user_input)},
        config=CONFIG,
        stream_mode='messages'
    ))
    st.session_state['message_history'].append({'role': 'assistant', 'content': response})
