import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import json
import os

KEY_FILE = 'fernet.key'
DATA_FILE = 'data.json'

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    return key

fernet = Fernet(load_key())

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def insert_data(user_id, text, passkey):
    data = load_data()
    encrypted_text = fernet.encrypt(text.encode()).decode()
    hashed_passkey = hash_passkey(passkey)
    data[user_id] = {"encrypted_text": encrypted_text, "passkey": hashed_passkey}
    save_data(data)
    st.success(f"Data stored securely for user: {user_id}")

def retrieve_data(user_id, passkey):
    data = load_data()
    if user_id not in data:
        st.error("No data found for this user.")
        return

    if st.session_state.failed_attempts.get(user_id, 0) >= 3:
        st.session_state.authorized = False
        st.warning("Too many failed attempts. Redirecting to login.")
        st.rerun()
        return

    hashed_input = hash_passkey(passkey)
    if hashed_input == data[user_id]["passkey"]:
        decrypted = fernet.decrypt(data[user_id]["encrypted_text"].encode()).decode()
        st.success(f"Decrypted Data: {decrypted}")
        st.session_state.failed_attempts[user_id] = 0  # reset after success
    else:
        st.session_state.failed_attempts[user_id] = st.session_state.failed_attempts.get(user_id, 0) + 1
        attempts_left = 3 - st.session_state.failed_attempts[user_id]
        st.error(f"Incorrect passkey. Attempts left: {attempts_left}")

def login_page():
    st.title("🔐 Reauthorization Required")
    username = st.text_input("Enter Admin Username")
    password = st.text_input("Enter Admin Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.authorized = True
            st.session_state.failed_attempts.clear()
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

def main():
    if 'authorized' not in st.session_state:
        st.session_state.authorized = True
    if 'failed_attempts' not in st.session_state:
        st.session_state.failed_attempts = {}

    if not st.session_state.authorized:
        login_page()
        return

    st.sidebar.title("🔐 Secure Data Storage")
    menu = st.sidebar.radio("Navigate", ["Home", "Insert Data", "Retrieve Data", "Login"])

    if menu == "Home":
        st.title("Welcome to Secure Data Encryption System")
        st.write("Use the sidebar to insert or retrieve encrypted data.")

    elif menu == "Insert Data":
        st.title("📥 Store Your Secure Data")
        user_id = st.text_input("Enter User ID")
        data = st.text_area("Enter Data to Encrypt")
        passkey = st.text_input("Set a Passkey", type="password")
        if st.button("Store Data"):
            if user_id and data and passkey:
                insert_data(user_id, data, passkey)
            else:
                st.warning("All fields are required.")

    elif menu == "Retrieve Data":
        st.title("🔓 Retrieve Your Encrypted Data")
        user_id = st.text_input("Enter Your User ID")
        passkey = st.text_input("Enter Your Passkey", type="password")
        if st.button("Decrypt Data"):
            if user_id and passkey:
                retrieve_data(user_id, passkey)
            else:
                st.warning("Both User ID and Passkey are required.")

    elif menu == "Login":
        login_page()

if __name__ == "__main__":
    main()
