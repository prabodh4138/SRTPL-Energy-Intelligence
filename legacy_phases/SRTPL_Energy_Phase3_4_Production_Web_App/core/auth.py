import hmac
import os
import streamlit as st

class AuthService:
    def is_authenticated(self):
        return bool(st.session_state.get("authenticated"))

    def login(self, username, password):
        admin_email = os.getenv("ADMIN_EMAIL", "")
        admin_token = os.getenv("ADMIN_TOKEN", "")
        if admin_email and admin_token and hmac.compare_digest(username, admin_email) and hmac.compare_digest(password, admin_token):
            st.session_state["authenticated"] = True
            st.session_state["role"] = "SUPER_ADMIN"
            st.session_state["user"] = username
            return True
        return False

    def logout(self):
        for key in ("authenticated", "role", "user"):
            st.session_state.pop(key, None)
