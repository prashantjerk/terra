package edu.lynchburg.terra.service;

import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import edu.lynchburg.terra.model.ParkingLog;
import edu.lynchburg.terra.repository.ParkingLogRepository;
import org.springframework.stereotype.Service;

@Service
public class ParkingService {

    private final ParkingLogRepository repository;

    public ParkingService(ParkingLogRepository repository) {
        this.repository = repository;
    }

    public ParkingSummaryResponse getLatestStatus() {
        return repository.findTopByOrderByRecordedAtDescIdDesc()
                .map(latest -> new ParkingSummaryResponse(latest.getRecordedAt(), latest.getNumCarsParked()))
                .orElse(new ParkingSummaryResponse(null, null));
    }

    public void updateParkingStatus(ParkingStatusUpdateRequest request) {
        if (request.getNumOfCarsParked() != null) {
            ParkingLog log = new ParkingLog(request.getNumOfCarsParked());
            repository.save(log);
        }
    }
}