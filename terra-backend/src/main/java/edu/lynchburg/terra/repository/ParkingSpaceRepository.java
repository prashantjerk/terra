package edu.lynchburg.terra.repository;

import edu.lynchburg.terra.model.ParkingSpace;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ParkingSpaceRepository extends JpaRepository<ParkingSpace, String> {
    List<ParkingSpace> findAllByOrderBySpaceIdAsc();
}
