import streamlit as st
import pandas as pd
import os
import io
import re
import zipfile
from datetime import datetime

st.set_page_config(page_title="XML Generator Tool", layout="centered")

st.title("📄 Report XML Generator")
st.markdown("Upload the input and database Excel files to generate XML files in a ZIP archive.")

# Upload files
input_file = st.file_uploader("Upload Input Excel File", type=["xlsx"])
db_file = st.file_uploader("Upload Database Excel File", type=["xlsx"])

if input_file and db_file:
    input_df = pd.read_excel(input_file)
    db_df = pd.read_excel(db_file)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for _, row in input_df.iterrows():
            input_report = str(row['reportName']).strip()
            input_fund = str(row['fundName']).strip()
            input_date = row.get('date', None)

            # Match report name
            db_filtered = db_df[
                db_df['RS_Report'].str.contains(input_report, case=False, na=False) &
                db_df['RS_ENGINE'].str.lower().eq('actuate') &
                db_df['RS_STATUS'].str.lower().eq('succeeded') &
                db_df['RS_PARAMETERS'].str.contains(f"PFondsMulti:\s*{input_fund}", na=False)
            ].copy()

            # Convert RS_START to datetime
            db_filtered['RSDateOnly'] = db_filtered['RS_START'].str.extract(r'(\d+\|\d+\|\d+)')[0].str.replace('|', '/')
            db_filtered['RSDateOnly'] = pd.to_datetime(db_filtered['RSDateOnly'], format='%m/%d/%Y', errors='coerce')

            if pd.notna(input_date):
                input_dt = pd.to_datetime(input_date, errors='coerce')
                db_filtered = db_filtered[db_filtered['RSDateOnly'] == input_dt]
            else:
                latest_date = db_filtered['RSDateOnly'].max()
                db_filtered = db_filtered[db_filtered['RSDateOnly'] == latest_date]

            for i, matched_row in db_filtered.iterrows():
                report_path = matched_row['RS_Report']
                xml_path = "/".join(report_path.split("/")[:-1])

                # Extract parameters into XML lines
                param_string = matched_row['RS_PARAMETERS']
                parameters = [p.strip() for p in param_string.split(';') if ':' in p]
                xml_params = ""
                for p in parameters:
                    key, val = map(str.strip, p.split(':', 1))
                    xml_params += f'    <parameter name="{key}">\n        <value>{val}</value>\n    </parameter>\n'

                report_format = matched_row['RS_FORMAT']
                xml_content = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    f'<reportTestcase name="{input_report}" format="{report_format}" pfad="{xml_path.rsplit(input_report,1)[0]}">\n'
                    f'{xml_params}'
                    '</reportTestcase>'
                )

                date_str = matched_row['RSDateOnly'].strftime("%Y-%m-%d") if pd.notna(matched_row['RSDateOnly']) else "nodate"
                filename = f"{input_report}_{input_fund}_{date_str}_{i}.xml"

                zipf.writestr(filename, xml_content)

    st.success("✅ XMLs generated!")
    st.download_button(
        label="📦 Download All XMLs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="generated_xmls.zip",
        mime="application/zip"
    )
