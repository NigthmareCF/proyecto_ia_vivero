package com.vivero.module.reports.controller;

import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.dto.GenerateReportRequestDto;
import com.vivero.module.reports.dto.NotificationChannelConfigRequestDto;
import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.NotifyReportRequestDto;
import com.vivero.module.reports.dto.ReportResponseDto;
import com.vivero.module.reports.dto.ToggleNotificationChannelRequestDto;
import com.vivero.module.reports.service.ReportService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/reports")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<ReportResponseDto>>> getAllReports() {
        return ResponseEntity.ok(ApiResponse.ok("Reports retrieved", reportService.getAllReports()));
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<ReportResponseDto>> getReportById(@PathVariable Long id) {
        return ResponseEntity.ok(ApiResponse.ok("Report retrieved", reportService.getReportById(id)));
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER')")
    public ResponseEntity<ApiResponse<ReportResponseDto>> generateReport(
            @Valid @RequestBody GenerateReportRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        ReportResponseDto response = reportService.generateReport(request, user.getEmail());
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Report generated successfully", response));
    }

    @GetMapping("/{id}/pdf")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<byte[]> downloadPdf(@PathVariable Long id) {
        byte[] pdfContent = reportService.getReportPdf(id);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(ContentDisposition.inline().filename("report-" + id + ".pdf").build());
        return ResponseEntity.ok().headers(headers).body(pdfContent);
    }

    @GetMapping("/public/{token}/pdf")
    public ResponseEntity<byte[]> downloadPublicPdf(@PathVariable String token) {
        byte[] pdfContent = reportService.getPublicReportPdf(token);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(ContentDisposition.inline().filename("shared-report.pdf").build());
        return ResponseEntity.ok().headers(headers).body(pdfContent);
    }

    @GetMapping("/notifications/config")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<NotificationConfigDto>>> getNotificationConfigs(
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        return ResponseEntity.ok(
                ApiResponse.ok("Notification configs retrieved", reportService.getNotificationConfigs(user.getEmail()))
        );
    }

    @GetMapping("/notifications/channels")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<NotificationChannel>>> getSupportedChannels() {
        return ResponseEntity.ok(
                ApiResponse.ok("Supported notification channels retrieved", reportService.getSupportedNotificationChannels())
        );
    }

    @PutMapping("/notifications/config")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<NotificationConfigDto>>> saveNotificationConfigs(
            @Valid @RequestBody List<NotificationConfigDto> request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        List<NotificationConfigDto> response = reportService.saveNotificationConfigs(request, user.getEmail());
        return ResponseEntity.ok(ApiResponse.ok("Notification configs saved", response));
    }

    @PutMapping("/notifications/config/{channel}")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<NotificationConfigDto>> saveNotificationConfig(
            @PathVariable NotificationChannel channel,
            @Valid @RequestBody NotificationChannelConfigRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        NotificationConfigDto response = reportService.saveNotificationConfig(channel, request, user.getEmail());
        return ResponseEntity.ok(ApiResponse.ok("Notification channel config saved", response));
    }

    @PatchMapping("/notifications/config/{channel}/toggle")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<NotificationConfigDto>> toggleNotificationChannel(
            @PathVariable NotificationChannel channel,
            @Valid @RequestBody ToggleNotificationChannelRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        NotificationConfigDto response = reportService.toggleNotificationChannel(channel, request.getActive(), user.getEmail());
        return ResponseEntity.ok(ApiResponse.ok("Notification channel toggled", response));
    }

    @PostMapping("/notify")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER')")
    public ResponseEntity<ApiResponse<String>> notifyReport(
            @Valid @RequestBody NotifyReportRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        int sentCount = reportService.notifyReport(request, user.getEmail());
        return ResponseEntity.ok(ApiResponse.ok("Report notified successfully", "Sent channels: " + sentCount));
    }
}
