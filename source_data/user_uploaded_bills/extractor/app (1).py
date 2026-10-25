import streamlit as st
import pandas as pd
import io
from concurrent.futures import ThreadPoolExecutor

# ---------- ENERGY BILL IMPORTS ----------
from extractor_main_full import extract_energy_bill_full
from extractor_md_full import extract_md_bill_data
from merge_clean_core import merge_and_clean_dataframes

# ---------- ENERGY RECEIPT IMPORT ----------
from extractor_receipt_full import extract_energy_receipt_data


st.set_page_config(
    page_title="Energy Document Processor",
    layout="wide"
)

st.title("Energy Document to Excel Converter")

st.write(
    "Upload Energy Bill or Energy Receipt PDFs and download Excel output."
)

# ---------- DOCUMENT TYPE ----------
doc_type = st.selectbox(
    "Select Document Type",
    ["Energy Bill", "Energy Receipt"]
)

# ---------- FILE UPLOAD ----------
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

# ---------- PROCESS ----------
if st.button("Process Documents"):
    if not uploaded_files:
        st.warning("Please upload at least one PDF.")
        st.stop()

    with st.spinner("Processing PDFs..."):

        # ==========================================================
        # ENERGY BILL PIPELINE
        # ==========================================================
        if doc_type == "Energy Bill":

            def process_bill_pdf(file):
                file.seek(0)
                main = extract_energy_bill_full(file, file.name)

                file.seek(0)
                md = extract_md_bill_data(file, file.name)

                return main, md

            with ThreadPoolExecutor(max_workers=6) as executor:
                results = list(executor.map(process_bill_pdf, uploaded_files))

            main_records = [r[0] for r in results]
            md_records = [r[1] for r in results]

            df_main = pd.DataFrame(main_records)
            df_md = pd.DataFrame(md_records)

            final_df = merge_and_clean_dataframes(df_main, df_md)

        # ==========================================================
        # ENERGY RECEIPT PIPELINE
        # ==========================================================
        else:  # Energy Receipt

            def process_receipt_pdf(file):
                file.seek(0)
                return extract_energy_receipt_data(file, file.name)

            with ThreadPoolExecutor(max_workers=6) as executor:
                receipt_records = list(
                    executor.map(process_receipt_pdf, uploaded_files)
                )

            final_df = pd.DataFrame(receipt_records)
            final_df.dropna(how="all", inplace=True)

    # ---------- OUTPUT ----------
    if final_df.empty:
        st.error("No valid data extracted.")
        st.stop()

    st.success("Processing completed successfully.")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sheet_name = "Energy_Bill_Data" if doc_type == "Energy Bill" else "Energy_Receipt_Data"
        final_df.to_excel(writer, index=False, sheet_name=sheet_name)

    st.download_button(
        label="Download Excel",
        data=output.getvalue(),
        file_name=f"{doc_type.replace(' ', '_')}_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
