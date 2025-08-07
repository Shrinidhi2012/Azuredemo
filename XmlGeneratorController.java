package com.example.xmlgenerator;

import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/xml-generator")
public class XmlGeneratorController {

    @PostMapping("/generate")
    public ResponseEntity<byte[]> generateXmlZip(
            @RequestParam("inputFile") MultipartFile inputFile,
            @RequestParam("dbFile") MultipartFile dbFile) {

        try {
            byte[] zipBytes = XmlGeneratorService.generateXmlZip(inputFile, dbFile);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            headers.setContentDisposition(ContentDisposition.attachment().filename("xmls.zip").build());

            return new ResponseEntity<>(zipBytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(("Error: " + e.getMessage()).getBytes());
        }
    }
}