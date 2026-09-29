package edu.lynchburg.terra.controller;

import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import edu.lynchburg.terra.service.ParkingService;
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

    @GetMapping("/status")
    public ResponseEntity<ParkingSummaryResponse> getStatus() {
        return ResponseEntity.ok(parkingService.getLatestStatus());
    }

    @PostMapping("/update")
    public ResponseEntity<String> updateStatus(@RequestBody ParkingStatusUpdateRequest request) {
        parkingService.updateParkingStatus(request);
        return ResponseEntity.ok("Status updated successfully.");
    }
}