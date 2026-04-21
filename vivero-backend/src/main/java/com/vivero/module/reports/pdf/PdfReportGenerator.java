package com.vivero.module.reports.pdf;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.borders.SolidBorder;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.ListItem;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import com.vivero.config.AppProperties;
import com.vivero.module.reports.dto.ReportFindingDto;
import com.vivero.module.reports.dto.ReportPlantDetailDto;
import com.vivero.module.reports.entity.Report;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.format.DateTimeFormatter;

/**
 * Generador de PDF para reportes del vivero.
 */
@Component
@RequiredArgsConstructor
public class PdfReportGenerator {

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final AppProperties appProperties;
    private final ObjectMapper objectMapper;

    public String generateAndStore(Report report) {
        Path reportsDir = Path.of(appProperties.getStorage().getImagesPath(), "reports");
        Path pdfPath = reportsDir.resolve("report-" + report.getId() + ".pdf");

        try {
            Files.createDirectories(reportsDir);
            Files.write(pdfPath, buildPdf(report));
            return pdfPath.toString();
        } catch (IOException ex) {
            throw new BusinessException("Failed to generate report PDF", "PDF_GENERATION_ERROR");
        }
    }

    public byte[] buildPdf(Report report) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            PdfWriter writer = new PdfWriter(outputStream);
            PdfDocument pdfDocument = new PdfDocument(writer);
            Document document = new Document(pdfDocument);

            java.util.List<ReportPlantDetailDto> plantDetails = readPlantDetails(report.getPlantDetailsJson());

            document.add(new Paragraph("Vivero-IA").setBold().setFontSize(20).setTextAlignment(TextAlignment.CENTER));
            document.add(new Paragraph("Reporte del vivero")
                    .setFontSize(11)
                    .setTextAlignment(TextAlignment.CENTER));
            document.add(new Paragraph(" "));
            document.add(new Paragraph("Reporte No. " + report.getId()).setBold());
            document.add(new Paragraph("Fecha de emision: " + DATE_FORMAT.format(report.getCreatedAt())));
            document.add(new Paragraph("Patrullaje No. " + report.getPatrolId()));
            document.add(new Paragraph("Emitido por: " + report.getGeneratedBy().getFullName()));
            document.add(new Paragraph(" "));

            Table table = new Table(UnitValue.createPercentArray(new float[] {1, 1, 1, 1, 1}))
                    .useAllAvailableWidth();
            addHeaderCell(table, "SANO");
            addHeaderCell(table, "ATENCION");
            addHeaderCell(table, "PELIGRO");
            addHeaderCell(table, "REVISION MANUAL");
            addHeaderCell(table, "INCONCLUSA");
            addValueCell(table, String.valueOf(report.getHealthyCount()));
            addValueCell(table, String.valueOf(report.getAttentionCount()));
            addValueCell(table, String.valueOf(report.getDangerCount()));
            addValueCell(table, String.valueOf(report.getManualReviewCount()));
            addValueCell(table, String.valueOf(report.getInconclusiveCount()));
            document.add(table);
            document.add(new Paragraph(" "));

            document.add(new Paragraph(buildExecutiveSummary(report)).setFontSize(11));
            if (report.getSummary() != null && !report.getSummary().isBlank()) {
                document.add(new Paragraph("Notas generales: " + report.getSummary()).setFontSize(11));
            }
            document.add(new Paragraph(" "));
            document.add(new Paragraph("Desglose por planta/maceta").setBold().setFontSize(14));

            if (plantDetails.isEmpty()) {
                document.add(new Paragraph("No se registraron hallazgos detallados para este reporte."));
            } else {
                for (ReportPlantDetailDto detail : plantDetails) {
                    document.add(new Paragraph(detail.getPlantGroupCode() + " - " + normalizeState(detail.getFinalState()))
                            .setBold()
                            .setFontSize(12));
                    document.add(new Paragraph(safeText(detail.getSummary())).setFontSize(11));
                    if (detail.getFindings() != null && !detail.getFindings().isEmpty()) {
                        com.itextpdf.layout.element.List findingsList = new com.itextpdf.layout.element.List();
                        for (ReportFindingDto finding : detail.getFindings()) {
                            findingsList.add(new ListItem(normalizeSide(finding.getSide()) + ": " + safeText(finding.getNote())));
                        }
                        document.add(findingsList);
                    }
                    document.add(new Paragraph(" "));
                }
            }
            document.close();

            return outputStream.toByteArray();
        } catch (IOException ex) {
            throw new BusinessException("Failed to build report PDF", "PDF_BUILD_ERROR");
        }
    }

    private String safeText(String value) {
        return value == null || value.isBlank() ? "Sin informacion adicional" : value;
    }

    private void addHeaderCell(Table table, String value) {
        table.addHeaderCell(new Cell()
                .add(new Paragraph(value).setBold().setFontSize(10))
                .setBackgroundColor(ColorConstants.LIGHT_GRAY)
                .setTextAlignment(TextAlignment.CENTER)
                .setBorder(new SolidBorder(ColorConstants.GRAY, 1)));
    }

    private void addValueCell(Table table, String value) {
        table.addCell(new Cell()
                .add(new Paragraph(value).setFontSize(12))
                .setTextAlignment(TextAlignment.CENTER)
                .setBorder(new SolidBorder(ColorConstants.GRAY, 1)));
    }

    private String buildExecutiveSummary(Report report) {
        return "El patrullaje registró "
                + report.getObservationsCount() + " plantas evaluadas: "
                + report.getHealthyCount() + " sanas, "
                + report.getAttentionCount() + " en atención, "
                + report.getDangerCount() + " en peligro, "
                + report.getManualReviewCount() + " para revisión manual y "
                + report.getInconclusiveCount() + " inconclusas.";
    }

    private java.util.List<ReportPlantDetailDto> readPlantDetails(String plantDetailsJson) {
        if (plantDetailsJson == null || plantDetailsJson.isBlank()) {
            return java.util.List.of();
        }
        try {
            return objectMapper.readValue(plantDetailsJson, new TypeReference<java.util.List<ReportPlantDetailDto>>() { });
        } catch (Exception ex) {
            throw new BusinessException("Failed to parse report detail payload", "PDF_DETAILS_PARSE_ERROR");
        }
    }

    private String normalizeState(String value) {
        if (value == null || value.isBlank()) {
            return "INCONCLUSA";
        }
        return value.trim().toUpperCase();
    }

    private String normalizeSide(String value) {
        if (value == null || value.isBlank()) {
            return "LADO NO ESPECIFICADO";
        }
        return value.trim().toUpperCase();
    }
}
