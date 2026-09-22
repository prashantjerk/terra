package edu.lynchburg.terra.service;

import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import edu.lynchburg.terra.model.ParkingSpace;
import edu.lynchburg.terra.repository.ParkingSpaceRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class ParkingService {

    private final ParkingSpaceRepository repository;

    public ParkingService(ParkingSpaceRepository repository) {
        this.repository = repository;
    }

    public void updateSpaceStatus(ParkingStatusUpdateRequest request) {
        ParkingSpace space = repository.findById(request.getSpaceId())
                .orElse(new ParkingSpace(request.getSpaceId(), request.getIsOccupied(), LocalDateTime.now()));

        space.setIsOccupied(request.getIsOccupied());
        space.setLastUpdated(LocalDateTime.now());

        repository.save(space);
    }

    public ParkingSummaryResponse getParkingSummary() {
        long availableCount = repository.countByIsOccupiedFalse();

        List<String> availableIds = repository.findByIsOccupiedFalse()
                .stream()
                .map(ParkingSpace::getSpaceId)
                .toList();

        List<ParkingSummaryResponse.SpaceStatus> allStatuses = repository.findAll()
                .stream()
                .map(s -> new ParkingSummaryResponse.SpaceStatus(s.getSpaceId(), s.getIsOccupied()))
                .toList();

        return new ParkingSummaryResponse(availableCount, availableIds, allStatuses);
    }
}