import streamlit as st
import pandas as pd
import zipfile
import io
import oracledb
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="XML Generator Tool", layout="centered")
st.title("📄 Report XML Generator")
st.markdown("Upload the input Excel file and click the button to generate XML files in a ZIP archive.")

input_file = st.file_uploader("Upload Input Excel File", type=["xlsx"])

# Oracle connection (replace with your credentials)
oracledb.init_oracle_client()
conn = oracledb.connect(
    user="your_user",
    password="your_password",
    dsn="your_host:your_port/your_service"
)

def fetch_and_generate(row, seen_keys):
    rpt, fund, dt = row['report'], row['fund'], row['date']
    key = (rpt, fund, dt.date() if pd.notna(dt) else None)
    if key in seen_keys:
        return []
    seen_keys.add(key)

    cursor = conn.cursor()

    query = """
        SELECT RS_REPORT, RS_PARAMETERS, RS_FORMAT, RS_START
        FROM KIRA_STAR.REPORT_STATISTICS
        WHERE LOWER(RS_ENGINE) = 'actuate'
          AND LOWER(RS_STATUS) = 'succeeded'
          AND LOWER(RS_REPORT) LIKE :rpt
          AND RS_PARAMETERS LIKE :fund
          AND ROWNUM <= 20
    """
    cursor.execute(query, {
        "rpt": f"%{rpt}%",
        "fund": f"%{fund}%"
    })

    rows = cursor.fetchall()
    if not rows:
        cursor.close()
        return []

    db_df = pd.DataFrame(rows, columns=["RS_REPORT", "RS_PARAMETERS", "RS_FORMAT", "RS_START"])
    db_df['RSDateTime'] = pd.to_datetime(db_df['RS_START'], errors='coerce')

    if pd.notna(dt):
        db_df = db_df[db_df['RSDateTime'].dt.date == dt.date()]
    else:
        latest_date = db_df['RSDateTime'].max()
        db_df = db_df[db_df['RSDateTime'].dt.date == latest_date.date()]

    db_df = db_df.sort_values(by='RSDateTime', ascending=False).reset_index(drop=True)

    xml_files = []

    for idx, m in db_df.iterrows():
        param_string = m['RS_PARAMETERS']
        report_format = m['RS_FORMAT']
        report_path = m['RS_REPORT']
        xml_path = "/".join(report_path.split("/")[:-1])

        parameters = [p.strip() for p in param_string.split(';') if ':' in p]
        xml_params = ""
        for p in parameters:
            keyval = p.split(':', 1)
            if len(keyval) == 2:
                k, v = map(str.strip, keyval)
                xml_params += f'  <parameter name="{k}">\n    <value>{v}</value>\n  </parameter>\n'

        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<reportTestcase name="{rpt}" format="{report_format}" pfad="{xml_path}">\n'
            f'{xml_params}</reportTestcase>'
        )

        date_str = m['RSDateTime'].strftime("%Y-%m-%d_%H-%M")
        filename = f"{rpt}_{fund}_{date_str}_{idx+1}.xml"
        xml_files.append((filename, xml_content))

    cursor.close()
    return xml_files

if input_file:
    input_df = pd.read_excel(input_file)
    input_df['report'] = input_df['report'].astype(str).str.strip().str.lower()
    input_df['fund'] = input_df['fund'].astype(str).str.strip()
    input_df['date'] = pd.to_datetime(input_df['date'], errors='coerce')

    zip_buffer = io.BytesIO()
    seen_keys = set()
    all_xmls = []

    with st.spinner("Generating XML files..."):
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_and_generate, row, seen_keys) for _, row in input_df.iterrows()]
            for i, future in enumerate(futures):
                xmls = future.result()
                all_xmls.extend(xmls)
                st.progress((i + 1) / len(futures))

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in all_xmls:
            zipf.writestr(filename, content)

    conn.close()
    st.success("✅ XMLs generated!")
    st.download_button(
        label="📦 Download All XMLs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="generated_xmls.zip",
        mime="application/zip"
    )
