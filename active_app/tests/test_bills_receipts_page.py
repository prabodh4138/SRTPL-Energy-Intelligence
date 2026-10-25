import sys
from pathlib import Path
import unittest.mock as mock

app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from pages import bills_receipts_center


def mock_selectbox(label, options, *args, **kwargs):
    return options[0] if options else "All"


def mock_columns(spec, *args, **kwargs):
    count = spec if isinstance(spec, int) else len(spec)
    cols = []
    for _ in range(count):
        col = mock.MagicMock()
        col.selectbox.side_effect = mock_selectbox
        cols.append(col)
    return cols


def mock_tabs(spec, *args, **kwargs):
    count = spec if isinstance(spec, int) else len(spec)
    return [mock.MagicMock() for _ in range(count)]


def test_bills_receipts_render():
    with mock.patch("streamlit.markdown"), \
         mock.patch("streamlit.title"), \
         mock.patch("streamlit.caption"), \
         mock.patch("streamlit.metric"), \
         mock.patch("streamlit.divider"), \
         mock.patch("streamlit.columns", side_effect=mock_columns), \
         mock.patch("streamlit.tabs", side_effect=mock_tabs), \
         mock.patch("streamlit.selectbox", side_effect=mock_selectbox), \
         mock.patch("streamlit.radio", return_value="⚡ Single Document Inspection (Live Preview)"), \
         mock.patch("streamlit.button", return_value=False), \
         mock.patch("streamlit.dataframe"), \
         mock.patch("streamlit.line_chart"), \
         mock.patch("streamlit.download_button"), \
         mock.patch("streamlit.subheader"), \
         mock.patch("streamlit.info"), \
         mock.patch("streamlit.success"), \
         mock.patch("streamlit.warning"), \
         mock.patch("streamlit.container", return_value=mock.MagicMock()):
        
        # Test rendering without exception
        bills_receipts_center.render()
