This is a Spring Boot-based Java backend project for generating XML files from Excel files.

🛠 USAGE:
- Build using: mvn clean install
- Run using: mvn spring-boot:run
- POST endpoint: http://localhost:8080/xml-generator/generate

Expected Form Data (multipart):
- inputFile: Excel file with columns: report, fund, [optional] date
- dbFile: Excel database with RS_Report, RS_ENGINE, RS_STATUS, RS_PARAMETERS, RS_START, RS_FORMAT

🎯 OUTPUT:
- Returns a zip file with XMLs that match your criteria.

🖥 FRONTEND:
- Use the accompanying Python Streamlit tool to upload files and call this API.