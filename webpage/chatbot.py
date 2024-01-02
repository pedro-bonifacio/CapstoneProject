import time
import streamlit as st
from chatbot_util.agent import AutoMentorChatbot
import hmac
import csv
from langchain.schema import AIMessage
import os
from chatbot_util.util import is_valid_api_key
import re


# TODO: Show car info by signal in the message (via index)

def initialize() -> None:
    """
    Initialize the app
    """
    page_bg_img = '''
        <style>
        [data-testid="ScrollToBottomContainer"] {
        background-image: url("https://i.imgur.com/1PBP7xR.png");
        background-size: cover;
        }
        .stChatFloatingInputContainer {
                background-color: rgba(0, 0, 0, 0)
        }
        [data-testid="stHeader"] {
                background-color: rgba(0, 0, 0, 0)
        }
        </style>
        '''
    st.markdown(page_bg_img, unsafe_allow_html=True)
    st.title("AutoMentor")

    if "chatbot" not in st.session_state:
        st.session_state.chatbot = AutoMentorChatbot(path="chatbot_util/car_dataset.csv")

    with st.sidebar:
        st.markdown(
            f"ChatBot in use: <font color='cyan'>{st.session_state.chatbot.__str__()}</font>", unsafe_allow_html=True
        )

    st.success(f"👋 Welcome back, {st.session_state['full_name']}!")


def check_password():
    """Returns True if the password is correct, otherwise returns False."""

    def load_user_data(csv_path):
        """Load user data from a CSV file."""
        user_data = {}
        with open(csv_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_data[row['Username']] = {'Password': row['Password'], 'Full Name': row['Full Name']}
        return user_data

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            username = st.text_input("Username", key="username")
            password = st.text_input("Password", type="password", key="password")

            api_key = st.text_input("Enter your GPT API key", type="password")
            os.environ["OPENAI_API_KEY"] = api_key.lstrip('"').rstrip('"')

            if st.form_submit_button("Log in") and username and password and api_key:
                if is_valid_api_key(api_key):
                    password_entered()
                else:
                    st.warning("Invalid API key. Please enter a valid GPT API key.")
            else:
                st.warning("Please enter all credentials.")

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        user_data = load_user_data(
            "./chatbot_util/customer_data.csv")  # because we use st.stop, even if this was run outside of check_password, this would always be re-executed if password was incorrect, so I left it here for easier reading
        if st.session_state["username"] in user_data and hmac.compare_digest(
                st.session_state["password"],
                user_data[st.session_state["username"]]['Password'],
        ):
            st.session_state["password_correct"] = True
            st.session_state["full_name"] = user_data[st.session_state["username"]]['Full Name']
            st.session_state["show_login_form"] = False
            del st.session_state["password"]  # Don't store the password.
            st.rerun()
        else:
            st.session_state["password_correct"] = False
            st.error("😕 User not known or password incorrect")

    if st.session_state.get("show_login_form", True):
        login_form()

    # Return True if the username + password is validated, otherwise False.
    return st.session_state.get("password_correct", False)


def display_history_messages():
    # Display chat messages from history on app rerun
    avatar_dict = {'assistant': '🤖', 'user': '😎'}
    for message in st.session_state.chatbot.chat_history:
        with st.chat_message(message['role'], avatar=avatar_dict[message['role']]):
            st.markdown(message['content'])


# [i]                                                                                            #
# [i] Display User Message                                                                       #
# [i]                                                                                            #

def display_user_msg(message: str):
    """
    Display user message in chat message container
    """
    with st.chat_message("user", avatar="😎"):
        st.markdown(message)
    st.session_state.chatbot.chat_history.append({"role": "user", "content": message})


# [i]                                                                                            #
# [i] Display User Message                                                                       #
# [i]                                                                                            #

def display_assistant_msg(message: str):
    """
    Display assistant message
    """

    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()

        # Simulate stream of response with milliseconds delay
        for i in range(len(message)):
            time.sleep(0.002)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(message[:i] + "▌")

        message_placeholder.markdown(message)

    st.session_state.chatbot.chat_history.append({"role": "assistant", "content": message})


def greeting():
    """
    Greeting message
    """
    if not st.session_state.chatbot.agent.memory.chat_memory.messages:
        initial_message = AIMessage(
            content=f"Greetings {st.session_state['full_name'].split()[0]}! I'm AutoMentor, your dedicated automotive assistant. Whether you're searching for the perfect car listing or looking to appraise the value of a vehicle you're considering selling, I'm here to assist. What can I do for you today?")
        st.session_state.chatbot.agent.memory.chat_memory.add_message(initial_message)
        display_assistant_msg(message=initial_message.content)


# [*]                                                                                            #
# [*] MAIN                                                                                       #
# [*]                                                                                            #

def app():
    login_successful = check_password()
    if not login_successful:
        st.stop()

    initialize()
    display_history_messages()
    greeting()

    if prompt := st.chat_input("Type your request..."):
        # [*] Request & Response #
        display_user_msg(message=prompt)
        assistant_response = st.session_state.chatbot.generate_response(
            message=prompt
        )
        display_assistant_msg(message=assistant_response['output'])

    # [i] Sidebar #
    with st.sidebar:
        with st.expander("Information"):
            st.text("💬 MEMORY")
            st.write(st.session_state.chatbot.agent.memory.chat_memory.messages)