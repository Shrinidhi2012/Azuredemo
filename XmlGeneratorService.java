package com.example.xmlgenerator;

import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import java.util.stream.Collectors;

public class XmlGeneratorService {

    public static byte[] generateXmlZip(MultipartFile inputFile, MultipartFile dbFile) throws Exception {
        List<Map<String, String>> inputRows = ExcelUtil.readExcel(inputFile);
        List<Map<String, String>> dbRows = ExcelUtil.readExcel(dbFile);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ZipOutputStream zipOut = new ZipOutputStream(baos);

        for (Map<String, String> input : inputRows) {
            String inputReport = input.get("report").trim();
            String inputFund = input.get("fund").trim();
            String inputDateStr = input.getOrDefault("date", "").trim();

            List<Map<String, String>> filtered = dbRows.stream()
                    .filter(row -> row.get("RS_Report").toLowerCase().contains(inputReport.toLowerCase()) &&
                                   row.get("RS_ENGINE").equalsIgnoreCase("actuate") &&
                                   row.get("RS_STATUS").equalsIgnoreCase("succeeded") &&
                                   row.get("RS_PARAMETERS").toLowerCase().contains(inputFund.toLowerCase()))
                    .collect(Collectors.toList());

            for (int i = 0; i < filtered.size(); i++) {
                Map<String, String> dbRow = filtered.get(i);
                String dateTime = dbRow.get("RS_START");
                LocalDateTime rsDateTime = LocalDateTime.parse(dateTime, DateTimeFormatter.ofPattern("MM/dd/yyyy hh:mm:ss a"));

                String xml = buildXml(inputReport, dbRow, rsDateTime);

                String dateStr = rsDateTime.format(DateTimeFormatter.ofPattern("MM-dd-yyyy_HH-mm"));
                String filename = inputReport + "_" + inputFund + "_" + dateStr + "_no_" + (i + 1) + ".xml";

                ZipEntry entry = new ZipEntry(filename);
                zipOut.putNextEntry(entry);
                zipOut.write(xml.getBytes());
                zipOut.closeEntry();
            }
        }

        zipOut.close();
        return baos.toByteArray();
    }

    private static String buildXml(String inputReport, Map<String, String> dbRow, LocalDateTime dateTime) {
        String reportPath = dbRow.get("RS_Report");
        String xmlPath = String.join("/", Arrays.asList(reportPath.split("/"))).replaceAll("/[^/]+$", "");
        String paramString = dbRow.get("RS_PARAMETERS");
        String format = dbRow.get("RS_FORMAT");

        StringBuilder xmlParams = new StringBuilder();
        for (String param : paramString.split(";")) {
            if (param.contains(":")) {
                String[] parts = param.split(":", 2);
                xmlParams.append("    <parameter name=\"")
                         .append(parts[0].trim())
                         .append("\">\n        <value>")
                         .append(parts[1].trim())
                         .append("</value>\n    </parameter>\n");
            }
        }

        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
                "<reportTestcase name=\"" + inputReport + "\" format=\"" + format + "\" pfad=\"" + xmlPath + "\">\n" +
                xmlParams +
                "</reportTestcase>";
    }
}