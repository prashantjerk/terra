package edu.lynchburg.terra.controller;

import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import edu.lynchburg.terra.service.ParkingService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/parking")
@CrossOrigin(origins = "http://localhost:3000")
public class ParkingController {

    private final ParkingService parkingService;

    public ParkingController(ParkingService parkingService) {
        this.parkingService = parkingService;
    }

    @PostMapping("/update")
    public ResponseEntity<String> updateParkingStatus(@Valid @RequestBody ParkingStatusUpdateRequest request) {
        parkingService.updateSpaceStatus(request);
        return ResponseEntity.ok("Parking space status updated successfully.");
    }

    @GetMapping("/status")
    public ResponseEntity<ParkingSummaryResponse> getParkingStatus() {
        ParkingSummaryResponse response = parkingService.getParkingSummary();
        return ResponseEntity.ok(response);
    }
}