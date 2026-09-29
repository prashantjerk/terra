package edu.lynchburg.terra.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "parking_logs")
public class ParkingLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "num_cars_parked", nullable = false)
    private Integer numCarsParked;

    @Column(name = "recorded_at")
    private LocalDateTime recordedAt = LocalDateTime.now();

    public ParkingLog() {}

    public ParkingLog(Integer numCarsParked) {
        this.numCarsParked = numCarsParked;
        this.recordedAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public Integer getNumCarsParked() { return numCarsParked; }
    public void setNumCarsParked(Integer numCarsParked) { this.numCarsParked = numCarsParked; }
    public LocalDateTime getRecordedAt() { return recordedAt; }
    public void setRecordedAt(LocalDateTime recordedAt) { this.recordedAt = recordedAt; }
}