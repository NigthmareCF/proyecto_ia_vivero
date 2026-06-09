package com.vivero.module.reports.service.impl;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.reports.dto.GenerateReportRequestDto;
import com.vivero.module.reports.dto.NotificationChannelConfigRequestDto;
import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.NotifyReportRequestDto;
import com.vivero.module.reports.dto.ReportPlantDetailDto;
import com.vivero.module.reports.dto.ReportResponseDto;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.mapper.ReportMapper;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.repository.NotificationConfigRepository;
import com.vivero.module.reports.repository.ReportRepository;
import com.vivero.module.reports.service.ReportService;
import com.vivero.module.reports.service.notification.NotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Implementación del módulo reports.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ReportServiceImpl implements ReportService {

    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");
    private final ReportRepository reportRepository;
    private final NotificationConfigRepository notificationConfigRepository;
    private final UserRepository userRepository;
    private final ReportMapper reportMapper;
    private final PdfReportGenerator pdfReportGenerator;
    private final List<NotificationService> notificationServices;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional(readOnly = true)
    public List<ReportResponseDto> getAllReports() {
        return reportRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(reportMapper::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public ReportResponseDto getReportById(Long id) {
        return reportMapper.toResponse(findReportOrThrow(id));
    }

    @Override
    @Transactional
    public ReportResponseDto generateReport(GenerateReportRequestDto request, String currentUserEmail) {
        validateCounts(request);
        User currentUser = findUserOrThrow(currentUserEmail);

        Report report = Objects.requireNonNull(
                Report.builder()
                        .patrolId(request.getPatrolId())
                        .generatedBy(currentUser)
                        .title(request.getTitle().trim())
                        .summary(normalizeText(request.getSummary()))
                        .observationsCount(request.getObservationsCount())
                        .healthyCount(request.getHealthyCount())
                        .attentionCount(request.getAttentionCount())
                        .dangerCount(request.getDangerCount())
                        .manualReviewCount(request.getManualReviewCount())
                        .inconclusiveCount(request.getInconclusiveCount())
                        .plantDetailsJson(writePlantDetails(request.getPlantDetails()))
                        .publicShareToken(generatePublicShareToken())
                        .build()
        );

        reportRepository.save(report);
        report.setPdfPath(pdfReportGenerator.generateAndStore(report));
        reportRepository.save(report);

        log.info("Reporte generado para patrullaje {} por {}", report.getPatrolId(), currentUser.getEmail());
        return reportMapper.toResponse(report);
    }

    @Override
    @Transactional
    public byte[] getReportPdf(Long id) {
        Report report = findReportOrThrow(id);
        return readPdfBytes(report, "report id: " + id);
    }

    @Override
    @Transactional
    public byte[] getPublicReportPdf(String publicShareToken) {
        Report report = reportRepository.findByPublicShareToken(publicShareToken)
                .orElseThrow(() -> new ResourceNotFoundException("Public report not found"));
        return readPdfBytes(report, "public report token");
    }

    @Override
    @Transactional(readOnly = true)
    public List<NotificationConfigDto> getNotificationConfigs(String currentUserEmail) {
        User currentUser = findUserOrThrow(currentUserEmail);
        return notificationConfigRepository.findByUserIdOrderByChannelAsc(currentUser.getId())
                .stream()
                .map(reportMapper::toConfigDto)
                .toList();
    }

    @Override
    @Transactional
    public List<NotificationConfigDto> saveNotificationConfigs(
            List<NotificationConfigDto> request,
            String currentUserEmail
    ) {
        if (request == null || request.isEmpty()) {
            throw new BusinessException("At least one notification config is required", "NOTIFICATION_CONFIG_REQUIRED");
        }

        User currentUser = findUserOrThrow(currentUserEmail);
        validateUniqueChannels(request);

        List<NotificationConfig> savedConfigs = request.stream()
                .map(configDto -> upsertConfig(currentUser, configDto))
                .toList();

        log.info("Configuraciones de notificación actualizadas para {}", currentUser.getEmail());
        return savedConfigs.stream()
                .map(reportMapper::toConfigDto)
                .toList();
    }

    @Override
    @Transactional
    public NotificationConfigDto saveNotificationConfig(
            NotificationChannel channel,
            NotificationChannelConfigRequestDto request,
            String currentUserEmail
    ) {
        User currentUser = findUserOrThrow(currentUserEmail);
        NotificationConfig config = upsertConfig(
                currentUser,
                NotificationConfigDto.builder()
                        .channel(channel)
                        .contactValue(request.getContactValue())
                        .active(request.getActive())
                        .build()
        );

        log.info("Configuración individual de {} actualizada para {}", channel, currentUser.getEmail());
        return reportMapper.toConfigDto(config);
    }

    @Override
    @Transactional
    public NotificationConfigDto toggleNotificationChannel(
            NotificationChannel channel,
            boolean active,
            String currentUserEmail
    ) {
        User currentUser = findUserOrThrow(currentUserEmail);
        NotificationConfig config = notificationConfigRepository.findByUserIdAndChannel(currentUser.getId(), channel)
                .orElseThrow(() -> new ResourceNotFoundException("Notification config not found for channel: " + channel));

        config.setActive(active);
        notificationConfigRepository.save(config);

        log.info("Canal {} {} para {}", channel, active ? "activado" : "desactivado", currentUser.getEmail());
        return reportMapper.toConfigDto(config);
    }

    @Override
    @Transactional(readOnly = true)
    public List<NotificationChannel> getSupportedNotificationChannels() {
        return List.of(NotificationChannel.values());
    }

    @Override
    @Transactional
    public int notifyReport(NotifyReportRequestDto request, String currentUserEmail) {
        User currentUser = findUserOrThrow(currentUserEmail);
        Report report = findReportOrThrow(request.getReportId());

        List<NotificationConfig> activeConfigs = notificationConfigRepository.findByUserIdAndActiveTrue(currentUser.getId());
        if (activeConfigs.isEmpty()) {
            throw new BusinessException("No active notification configs found", "NO_ACTIVE_NOTIFICATION_CONFIG");
        }

        EnumSet<NotificationChannel> selectedChannels = request.getChannels() == null || request.getChannels().isEmpty()
                ? EnumSet.allOf(NotificationChannel.class)
                : EnumSet.copyOf(request.getChannels());

        Map<NotificationChannel, NotificationService> servicesByChannel = notificationServices.stream()
                .collect(Collectors.toMap(NotificationService::getChannel, Function.identity()));

        byte[] pdfContent = pdfReportGenerator.buildPdf(report);
        int sent = 0;

        for (NotificationConfig config : activeConfigs) {
            if (!selectedChannels.contains(config.getChannel())) {
                continue;
            }

            NotificationService notificationService = servicesByChannel.get(config.getChannel());
            if (notificationService == null) {
                throw new BusinessException(
                        "Notification channel not supported: " + config.getChannel(),
                        "NOTIFICATION_CHANNEL_NOT_SUPPORTED"
                );
            }

            notificationService.sendReportNotification(report, config, pdfContent);
            sent++;
        }

        if (sent == 0) {
            throw new BusinessException("No matching notification configs found", "NO_MATCHING_NOTIFICATION_CONFIG");
        }

        log.info("Reporte {} notificado por {} canales para {}", report.getId(), sent, currentUser.getEmail());
        return sent;
    }

    private void validateCounts(GenerateReportRequestDto request) {
        int total = request.getHealthyCount()
                + request.getAttentionCount()
                + request.getDangerCount()
                + request.getManualReviewCount()
                + request.getInconclusiveCount();
        if (total != request.getObservationsCount()) {
            throw new BusinessException(
                    "State counts must match total observations",
                    "INVALID_REPORT_COUNTS"
            );
        }
    }

    private void validateUniqueChannels(List<NotificationConfigDto> request) {
        Set<NotificationChannel> seenChannels = new HashSet<>();
        for (NotificationConfigDto configDto : request) {
            if (!seenChannels.add(configDto.getChannel())) {
                throw new BusinessException(
                        "Duplicate notification channel in request: " + configDto.getChannel(),
                        "DUPLICATE_NOTIFICATION_CHANNEL"
                );
            }
        }
    }

    private NotificationConfig upsertConfig(User currentUser, NotificationConfigDto configDto) {
        validateNotificationConfig(configDto, currentUser);

        NotificationConfig config = notificationConfigRepository
                .findByUserIdAndChannel(currentUser.getId(), configDto.getChannel())
                .orElseGet(() -> NotificationConfig.builder()
                        .user(currentUser)
                        .channel(configDto.getChannel())
                        .build());

        config.setContactValue(resolveStoredContactValue(currentUser, configDto));
        config.setActive(Boolean.TRUE.equals(configDto.getActive()));

        return notificationConfigRepository.save(config);
    }

    private void validateNotificationConfig(NotificationConfigDto configDto, User currentUser) {
        if (configDto.getChannel() == null) {
            throw new BusinessException("Notification channel is required", "CHANNEL_REQUIRED");
        }

        String contactValue = configDto.getContactValue() == null ? null : configDto.getContactValue().trim();

        switch (configDto.getChannel()) {
            case EMAIL -> {
                if (contactValue == null || contactValue.isEmpty()) {
                    throw new BusinessException("Contact value is required", "CONTACT_VALUE_REQUIRED");
                }
                validateEmail(contactValue);
            }
        }
    }

    private void validateEmail(String contactValue) {
        if (!EMAIL_PATTERN.matcher(contactValue).matches()) {
            throw new BusinessException("Invalid email format", "INVALID_EMAIL_CONTACT");
        }
    }

    private String resolveStoredContactValue(User currentUser, NotificationConfigDto configDto) {
        return configDto.getContactValue() == null ? null : configDto.getContactValue().trim();
    }

    private @NonNull Report findReportOrThrow(@NonNull Long id) {
        return reportRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Report not found with id: " + id));
    }

    private byte[] readPdfBytes(Report report, String reference) {
        try {
            if (report.getPdfPath() == null
                    || report.getPdfPath().isBlank()
                    || !Files.exists(Path.of(report.getPdfPath()))) {
                report.setPdfPath(pdfReportGenerator.generateAndStore(report));
                reportRepository.save(report);
            }
            return Files.readAllBytes(Path.of(report.getPdfPath()));
        } catch (Exception ex) {
            throw new BusinessException("Could not generate or read PDF for " + reference, "PDF_READ_ERROR");
        }
    }

    private String generatePublicShareToken() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    private @NonNull User findUserOrThrow(@NonNull String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
    }

    private String normalizeText(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }

    private String writePlantDetails(List<ReportPlantDetailDto> plantDetails) {
        try {
            return objectMapper.writeValueAsString(plantDetails == null ? List.of() : plantDetails);
        } catch (Exception ex) {
            throw new BusinessException("Could not serialize report plant details", "REPORT_DETAILS_SERIALIZATION_ERROR");
        }
    }
}
