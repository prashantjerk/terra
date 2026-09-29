package edu.lynchburg.terra.repository;

import edu.lynchburg.terra.model.ParkingLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface ParkingLogRepository extends JpaRepository<ParkingLog, Long> {
    Optional<ParkingLog> findTopByOrderByRecordedAtDesc();
}