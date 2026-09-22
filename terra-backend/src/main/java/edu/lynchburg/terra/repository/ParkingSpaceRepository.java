package edu.lynchburg.terra.repository;

import edu.lynchburg.terra.model.ParkingSpace;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ParkingSpaceRepository extends JpaRepository<ParkingSpace, String> {
    List<ParkingSpace> findByIsOccupiedFalse();
    long countByIsOccupiedFalse();
}