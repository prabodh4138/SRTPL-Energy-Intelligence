"""SRTPL Power Intelligence — Reports module entrypoint.
Delegates to the Custom View Builder and Report Studio.
"""
from __future__ import annotations

import streamlit as st
from pages.reports_export_center import render as render_reports_studio


def render() -> None:
    """Renders the comprehensive Report Center and Custom View Studio."""
    render_reports_studio()


if __name__ == "__main__":
    render()
