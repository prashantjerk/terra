package edu.lynchburg.terra.service;

import edu.lynchburg.terra.dto.*;
import edu.lynchburg.terra.model.ParkingSpace;
import edu.lynchburg.terra.repository.ParkingSpaceRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

@Service
@Transactional(readOnly = true)
public class ParkingSpaceService {
    private final ParkingSpaceRepository repository;
    public ParkingSpaceService(ParkingSpaceRepository repository) { this.repository = repository; }

    public List<ParkingSpaceResponse> list() {
        return repository.findAllByOrderBySpaceIdAsc().stream().map(ParkingSpaceResponse::from).toList();
    }
    private ParkingSpace find(String id) {
        return repository.findById(id).orElseThrow(() ->
            new ResponseStatusException(HttpStatus.NOT_FOUND, "Parking space not found"));
    }
    public ParkingSpaceResponse get(String id) { return ParkingSpaceResponse.from(find(id)); }

    @Transactional
    public ParkingSpaceResponse create(CreateParkingSpaceRequest request) {
        if (repository.existsById(request.spaceId())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Parking space already exists");
        }
        // persist a new entity; nullable version lets Spring Data distinguish insert from update.
        ParkingSpace space = new ParkingSpace(request.spaceId(), request.label().trim(), request.occupied());
        return ParkingSpaceResponse.from(repository.saveAndFlush(space));
    }
    @Transactional
    public ParkingSpaceResponse update(String id, UpdateParkingSpaceRequest request) {
        ParkingSpace space = find(id);
        space.updateOccupancy(request.occupied());
        return ParkingSpaceResponse.from(repository.saveAndFlush(space));
    }
    public ParkingSpaceSummaryResponse summary() {
        List<ParkingSpace> spaces = repository.findAllByOrderBySpaceIdAsc();
        long occupied = spaces.stream().filter(s -> Boolean.TRUE.equals(s.getOccupied())).count();
        long available = spaces.stream().filter(s -> Boolean.FALSE.equals(s.getOccupied())).count();
        return new ParkingSpaceSummaryResponse(spaces.size(), occupied, available,
                                               spaces.size() - occupied - available);
    }
}
