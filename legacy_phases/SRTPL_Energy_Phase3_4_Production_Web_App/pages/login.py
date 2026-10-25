import streamlit as st

def render(auth):
    st.title("SRTPL Power Consumption Analytics")
    st.subheader("Secure Login")
    with st.form("login"):
        username = st.text_input("Username / Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
    if submitted:
        if auth.login(username, password):
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid credentials.")
