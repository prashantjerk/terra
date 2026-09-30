package edu.lynchburg.terra.controller;

import edu.lynchburg.terra.dto.*;
import edu.lynchburg.terra.service.ParkingSpaceService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/api/v1/parking/spaces")
@CrossOrigin(origins = "http://localhost:3000")
public class ParkingSpaceController {
    private final ParkingSpaceService service;
    public ParkingSpaceController(ParkingSpaceService service) { this.service = service; }

    @GetMapping
    public List<ParkingSpaceResponse> list() { return service.list(); }
    @GetMapping("/summary")
    public ParkingSpaceSummaryResponse summary() { return service.summary(); }
    @GetMapping("/{spaceId}")
    public ParkingSpaceResponse get(@PathVariable String spaceId) { return service.get(spaceId); }
    @PostMapping
    public ResponseEntity<ParkingSpaceResponse> create(@Valid @RequestBody CreateParkingSpaceRequest request) {
        return ResponseEntity.created(URI.create("/api/v1/parking/spaces/" + request.spaceId()))
            .body(service.create(request));
    }
    @PutMapping("/{spaceId}/status")
    public ParkingSpaceResponse update(@PathVariable String spaceId,
                                       @Valid @RequestBody UpdateParkingSpaceRequest request) {
        return service.update(spaceId, request);
    }
}
