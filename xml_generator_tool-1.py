
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

            # FILTERING STEP
            db_filtered = db_df[
                db_df['RS_Report'].str.contains(input_report, case=False, na=False) &
                db_df['RS_ENGINE'].str.lower().eq('actuate') &
                db_df['RS_STATUS'].str.lower().eq('succeeded') &
                db_df['RS_PARAMETERS'].str.contains(f"pFondsMulti\s*:\s*[^;]*{input_fund}[^;]*", case=False, na=False)
            ].copy()

            # ✅ CHANGE 1: Parse full datetime with time (mm/dd/yyyy hh:mm:ss AM/PM)
            db_filtered['RSDateTime'] = pd.to_datetime(
                db_filtered['RS_START'].str.replace('|', '/'),
                format='%m/%d/%Y %I:%M:%S %p',
                errors='coerce'
            )

            if pd.notna(input_date):
                input_dt = pd.to_datetime(input_date, errors='coerce')
                # Keep all with same date (including time)
                db_filtered = db_filtered[db_filtered['RSDateTime'].dt.date == input_dt.date()]
            else:
                # Get most recent date and time for fallback
                latest_datetime = db_filtered['RSDateTime'].max()
                db_filtered = db_filtered[db_filtered['RSDateTime'].dt.date == latest_datetime.date()]

            # ✅ CHANGE 2: Sort by datetime descending to number 1 = latest, n = oldest
            db_filtered = db_filtered.sort_values(by='RSDateTime', ascending=False).reset_index(drop=True)

            for idx, matched_row in db_filtered.iterrows():
                report_path = matched_row['RS_Report']
                xml_path = "/".join(report_path.split("/")[:-1])

                param_string = matched_row['RS_PARAMETERS']
                parameters = [p.strip() for p in param_string.split(';') if ':' in p]
                xml_params = ""

                for p in parameters:
                    key, val = map(str.strip, p.split(':', 1))
                    # ✅ CHANGE 3: Convert pFondsMulti comma to pipe in output
                    if key.lower() == "pfondsmulti":
                        val = val.replace(",", "|")
                    xml_params += f'    <parameter name="{key}">\n        <value>{val}</value>\n    </parameter>\n'

                report_format = matched_row['RS_FORMAT']
                xml_content = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    f'<reportTestcase name="{input_report}" format="{report_format}" pfad="{xml_path.rsplit(input_report,1)[0]}">\n'
                    f'{xml_params}'
                    '</reportTestcase>'
                )

                # ✅ CHANGE 2 CONTINUED: Use idx+1 to number files properly
                date_str = matched_row['RSDateTime'].strftime("%Y-%m-%d_%H-%M")
                filename = f"{input_report}_{input_fund}_{date_str}_#{idx+1}.xml"

                zipf.writestr(filename, xml_content)

    st.success("✅ XMLs generated!")
    st.download_button(
        label="📦 Download All XMLs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="generated_xmls.zip",
        mime="application/zip"
    )
