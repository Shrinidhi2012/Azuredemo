package com.example.xmlgenerator;

import org.apache.poi.ss.usermodel.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.*;

public class ExcelUtil {

    public static List<Map<String, String>> readExcel(MultipartFile file) throws Exception {
        List<Map<String, String>> rows = new ArrayList<>();

        try (InputStream inputStream = file.getInputStream();
             Workbook workbook = WorkbookFactory.create(inputStream)) {

            Sheet sheet = workbook.getSheetAt(0);
            Row header = sheet.getRow(0);
            List<String> headers = new ArrayList<>();

            for (Cell cell : header) {
                headers.add(cell.getStringCellValue());
            }

            for (int i = 1; i <= sheet.getLastRowNum(); i++) {
                Row row = sheet.getRow(i);
                Map<String, String> rowData = new HashMap<>();
                for (int j = 0; j < headers.size(); j++) {
                    Cell cell = row.getCell(j, Row.MissingCellPolicy.CREATE_NULL_AS_BLANK);
                    rowData.put(headers.get(j), cell.toString());
                }
                rows.add(rowData);
            }
        }

        return rows;
    }
}