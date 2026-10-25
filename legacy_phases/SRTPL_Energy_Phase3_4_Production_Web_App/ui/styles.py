import streamlit as st

def load_styles():
    st.markdown(
        '''
        <style>
        .block-container { padding-top: 1.2rem; }
        [data-testid="stMetricValue"] { font-size: 1.7rem; }
        </style>
        ''',
        unsafe_allow_html=True,
    )
