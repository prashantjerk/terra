package edu.lynchburg.terra.controller;

import edu.lynchburg.terra.dto.ParkingPhotoResult;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import edu.lynchburg.terra.service.PiClient;

@RestController
@RequestMapping("/api/v1/parking/photos")
@CrossOrigin(origins = "http://localhost:3000", exposedHeaders = "Retry-After")
public class ParkingPhotoController {
    public record PhotoRequest(String photo) {}

    private final PiClient pi;
    private final JdbcTemplate database;
    private final String url;

    public ParkingPhotoController(PiClient pi, JdbcTemplate database,
                                  @Value("${terra.photo-pi-url:}") String url) {
        this.pi = pi;
        this.database = database;
        this.url = url.replaceAll("/+$", "");
    }

    @GetMapping
    public ResponseEntity<?> photos() {
        if (url.isBlank()) return unavailable("Saved-photo service is not configured.");
        try {
            return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .body(pi.listPhotos(url + "/photos"));
        } catch (RestClientException | IllegalStateException e) {
            return unavailable("Could not load the saved photos from the Pi.");
        }
    }

    @PostMapping(value = "/check", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> check(@RequestBody PhotoRequest request) {
        String name = request.photo();
        if (name == null || name.isBlank() || name.length() > 255)
            return ResponseEntity.badRequest().body(Map.of("error", "Select a saved photo."));
        if (url.isBlank()) return unavailable("Saved-photo service is not configured.");
        ParkingPhotoResult result;
        try {
            result = pi.checkPhoto(url + "/check-photo", name);
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().value() == 404)
                return ResponseEntity.status(404).body(Map.of("error", "This photo is no longer on the Pi."));
            if (e.getStatusCode().value() == 422)
                return ResponseEntity.status(422).body(Map.of("error", "Could not analyze this photo. Check its framing and format."));
            return unavailable("The Pi could not check this photo. Try again shortly.");
        } catch (RestClientException | IllegalStateException e) {
            return unavailable("Could not reach the saved-photo service on the Pi.");
        }
        if (result == null || !result.validFor(name))
            return unavailable("The Pi returned an invalid parking result.");

        String occupiedSpaces = result.spaces().entrySet().stream()
            .filter(entry -> "occupied".equals(entry.getValue()))
            .map(Map.Entry::getKey).sorted().collect(Collectors.joining(","));
        database.update("""
            INSERT INTO parking_photo_results (photo_id, checked_at, capacity, occupied, occupied_spaces)
            VALUES (?, ?, ?, ?, ?)
            """, result.photo(), result.checkedAt(), result.capacity(), result.occupied(), occupiedSpaces);
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(result);
    }

    private ResponseEntity<?> unavailable(String message) {
        return ResponseEntity.status(503).header("Retry-After", "10").body(Map.of("error", message));
    }
}
