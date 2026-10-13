package edu.lynchburg.terra.controller;

import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import edu.lynchburg.terra.service.ParkingService;
import edu.lynchburg.terra.service.RefreshService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/parking")
@CrossOrigin(origins = "http://localhost:3000", exposedHeaders = {"Retry-After"})
public class ParkingController {

    private final ParkingService parkingService;

    private final RefreshService refreshService;

    public ParkingController(ParkingService parkingService, RefreshService refreshService) {
        this.refreshService = refreshService;
        this.parkingService = parkingService;
    }

    @GetMapping("/status")
    public ResponseEntity<ParkingSummaryResponse> getStatus() {
        return ResponseEntity.ok().header("Cache-Control","no-store").body(parkingService.getLatestStatus());
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh() {
        try { return ResponseEntity.ok().header("Cache-Control","no-store").body(refreshService.refresh()); }
        catch (RuntimeException e) {
            return ResponseEntity.status(503).header("Retry-After","10")
                .body(java.util.Map.of("error","Pi unavailable. Previous result remains unchanged."));
        }
    }

    @PostMapping("/update")
    public ResponseEntity<String> updateStatus(@Valid @RequestBody ParkingStatusUpdateRequest request) {
        parkingService.updateParkingStatus(request);
        return ResponseEntity.ok("Status updated successfully.");
    }
}
