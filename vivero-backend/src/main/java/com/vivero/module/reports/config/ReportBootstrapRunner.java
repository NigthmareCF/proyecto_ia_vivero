package com.vivero.module.reports.config;

import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.repository.ReportRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

/**
 * Completa artefactos faltantes de reportes seed al iniciar la aplicación.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ReportBootstrapRunner implements ApplicationRunner {

    private final ReportRepository reportRepository;
    private final PdfReportGenerator pdfReportGenerator;

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        for (Report report : reportRepository.findAllByOrderByCreatedAtDesc()) {
            if (report.getPublicShareToken() == null || report.getPublicShareToken().isBlank()) {
                report.setPublicShareToken(UUID.randomUUID().toString().replace("-", ""));
                log.info("Token publico generado para reporte seed {}", report.getId());
            }
            if (report.getPdfPath() == null || report.getPdfPath().isBlank()) {
                report.setPdfPath(pdfReportGenerator.generateAndStore(report));
                log.info("PDF generado para reporte seed {}", report.getId());
            }
        }
    }
}
