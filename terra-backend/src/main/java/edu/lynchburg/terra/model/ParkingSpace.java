package edu.lynchburg.terra.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "parking_spaces")
public class ParkingSpace {
    @Id
    @Column(name = "space_id", nullable = false, unique = true)
    private String spaceId;

    @Column(name = "is_occupied", nullable = false)
    private Boolean isOccupied;

    @Column(name = "last_updated")
    private LocalDateTime lastUpdated;

    public ParkingSpace() {}

    public ParkingSpace(String spaceId, Boolean isOccupied, LocalDateTime lastUpdated) {
        this.spaceId = spaceId;
        this.isOccupied = isOccupied;
        this.lastUpdated = lastUpdated;
    }

    public String getSpaceId() { return spaceId; }
    public void setSpaceId(String spaceId) { this.spaceId = spaceId; }

    public Boolean getIsOccupied() { return isOccupied; }
    public void setIsOccupied(Boolean isOccupied) { this.isOccupied = isOccupied; }

    public LocalDateTime getLastUpdated() { return lastUpdated; }
    public void setLastUpdated(LocalDateTime lastUpdated) { this.lastUpdated = lastUpdated; }
}