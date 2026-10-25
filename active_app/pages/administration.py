import streamlit as st
def render():
    st.title("Administration")
    st.write("Users • Roles • Permissions • KPI configuration • Validation rules • System configuration")
    st.warning("Production role/RLS enforcement must be completed before deployment.")
