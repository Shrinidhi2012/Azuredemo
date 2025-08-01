import streamlit as st
import pandas as pd
from lxml import etree
import os
import zipfile

st.title("📄 XML Report Generator (Excel-Based)")

uploaded_file = st.file_uploader("Upload the Excel file with report run data", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        report_name = st.text_input("Enter report name (e.g., IWB-CSV):")
        num_files = st.number_input("Number of recent successful XMLs to generate:", min_value=1, max_value=20, value=5)

        if st.button("Generate & Download ZIP"):
            filtered_df = df[
                df["RS_REPORT"].str.contains(report_name, case=False, na=False) &
                (df["RS_STATUS"].str.lower() == "succeeded") &
                (df["RS_ENGINE"].str.lower() == "actuate")
            ].sort_values(by=["RS_END", "RS_START"], ascending=False).head(num_files)

            if filtered_df.empty:
                st.error("🚫 No matching successful Actuate runs found.")
            else:
                os.makedirs("generated_xmls", exist_ok=True)

                zip_path = "generated_xmls/xml_reports.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for i, row in filtered_df.iterrows():
                        root = etree.Element(
                            "reportTestCase",
                            name=report_name,
                            format=row["RS_FORMAT"].lower(),
                            pfad=row["RS_REPORT"].rsplit(report_name, 1)[0]
                        )

                        for pair in str(row["RS_PARAMETERS"]).split(";"):
                            if ":" not in pair:
                                continue
                            key, value = map(str.strip, pair.split(":", 1))
                            param = etree.SubElement(root, "parameter", name=key)
                            val = etree.SubElement(param, "value")
                            val.text = value

                        file_name = f"report_{i+1}.xml"
                        file_path = os.path.join("generated_xmls", file_name)
                        tree = etree.ElementTree(root)
                        tree.write(file_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

                        zipf.write(file_path, arcname=file_name)

                # Show ZIP download button
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="📦 Download All XMLs as ZIP",
                        data=f,
                        file_name="xml_reports.zip",
                        mime="application/zip"
                    )

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
