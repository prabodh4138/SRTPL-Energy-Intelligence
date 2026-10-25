import streamlit as st


def load_styles():
    st.markdown(
        """
        <style>
        /* SRTPL Energy Intelligence — Design System from HTML Prototype */
        :root {
            --bg: #08111f;
            --p: #111d2d;
            --line: #29394d;
            --t: #e6edf7;
            --m: #91a5bd;
            --teal: #32c4d0;
            --g: #55d6a3;
            --a: #f4c66d;
            --r: #ff8795;
        }

        /* Global Theme */
        .stApp {
            background-color: #08111f;
            color: #e6edf7;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1550px;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0b1423 !important;
            border-right: 1px solid #29394d;
        }

        /* Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #111d2d;
            border: 1px solid #29394d;
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }

        div[data-testid="stMetricLabel"] {
            color: #88a0ba !important;
            font-size: 0.75rem !important;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 750;
        }

        div[data-testid="stMetricValue"] {
            color: #e6edf7 !important;
            font-size: 1.75rem !important;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        /* Buttons */
        button[kind="primary"] {
            background: linear-gradient(135deg, #087f8b, #0ea5b7) !important;
            border: 1px solid #0e9ca8 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }

        button[kind="secondary"] {
            background-color: #1a2a3e !important;
            border: 1px solid #344b64 !important;
            color: #e7f0fa !important;
            border-radius: 8px !important;
        }

        button:hover {
            border-color: #32c4d0 !important;
        }

        /* DataFrames & Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid #29394d;
            border-radius: 10px;
            background-color: #111d2d;
            overflow: hidden;
        }

        /* Expanders & Containers */
        div[data-testid="stExpander"] {
            background-color: #111d2d;
            border: 1px solid #29394d !important;
            border-radius: 10px;
        }

        /* Custom HTML Prototype Classes */
        .eyebrow {
            font-size: 10px;
            color: #88a0ba;
            letter-spacing: .14em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .tag-pill {
            display: inline-block;
            border-radius: 99px;
            padding: 3px 9px;
            background: #203247;
            color: #bdd0e4;
            font-size: 11px;
            font-weight: 600;
        }

        .status-good {
            color: #55d6a3;
            font-weight: 600;
        }

        .status-warn {
            color: #f4c66d;
            font-weight: 600;
        }

        .status-bad {
            color: #ff8795;
            font-weight: 600;
        }

        .card-custom {
            background: #111d2d;
            border: 1px solid #29394d;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }

        .banner-warning {
            padding: 12px 16px;
            background: #2b2517;
            border: 1px solid #69552b;
            border-radius: 9px;
            color: #f6d68d;
            font-size: 13px;
            margin-bottom: 18px;
        }

        .barrow {
            display: grid;
            grid-template-columns: 55px 1fr 45px;
            gap: 10px;
            align-items: center;
            font-size: 12px;
            margin: 12px 0;
        }

        .barbg {
            height: 9px;
            border-radius: 9px;
            background: #293b50;
            overflow: hidden;
        }

        .barfill {
            height: 100%;
            border-radius: 9px;
            background: #32c4d0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
