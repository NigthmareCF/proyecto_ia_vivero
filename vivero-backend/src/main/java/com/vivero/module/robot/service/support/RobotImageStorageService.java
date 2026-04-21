package com.vivero.module.robot.service.support;

import com.vivero.config.AppProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.UUID;

/**
 * Guarda imágenes del robot en almacenamiento local del backend.
 */
@Service
@RequiredArgsConstructor
public class RobotImageStorageService {

    private static final DateTimeFormatter FOLDER_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter FILE_FORMAT = DateTimeFormatter.ofPattern("HHmmss");

    private final AppProperties appProperties;

    public List<StoredRobotImage> storeObservationImages(String robotId, List<String> imagesBase64, String mimeType) {
        List<StoredRobotImage> storedImages = new ArrayList<>();
        String normalizedMimeType = normalizeMimeType(mimeType);
        String extension = resolveExtension(normalizedMimeType);
        LocalDateTime now = LocalDateTime.now();
        Path baseDir = Paths.get(appProperties.getStorage().getImagesPath(), "robot-observations", robotId, now.format(FOLDER_FORMAT));

        try {
            Files.createDirectories(baseDir);
            for (int index = 0; index < imagesBase64.size(); index++) {
                String fileName = now.format(FILE_FORMAT) + "-" + UUID.randomUUID() + "-" + (index + 1) + "." + extension;
                Path fullPath = baseDir.resolve(fileName);
                Files.write(fullPath, decodeBase64(imagesBase64.get(index)), StandardOpenOption.CREATE_NEW);
                storedImages.add(new StoredRobotImage(fullPath.toString(), normalizedMimeType, index));
            }
            return storedImages;
        } catch (IOException ex) {
            throw new IllegalStateException("Could not store robot observation images", ex);
        }
    }

    private byte[] decodeBase64(String rawBase64) {
        String value = rawBase64;
        int separator = rawBase64.indexOf(',');
        if (separator >= 0) {
            value = rawBase64.substring(separator + 1);
        }
        return Base64.getDecoder().decode(value);
    }

    private String normalizeMimeType(String mimeType) {
        if (mimeType == null || mimeType.isBlank()) {
            return "image/jpeg";
        }
        return mimeType.trim().toLowerCase();
    }

    private String resolveExtension(String mimeType) {
        return switch (mimeType) {
            case "image/png" -> "png";
            case "image/webp" -> "webp";
            default -> "jpg";
        };
    }

    public record StoredRobotImage(String filePath, String mimeType, int sortOrder) {
    }
}
