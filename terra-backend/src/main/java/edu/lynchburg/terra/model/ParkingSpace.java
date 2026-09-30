package edu.lynchburg.terra.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "parking_spaces")
public class ParkingSpace {
    @Id
    @Column(name = "space_id", length = 32)
    private String spaceId;
    @Column(nullable = false, length = 100)
    private String label;
    // null means not yet observed, rather than vacant.
    @Column(name = "is_occupied")
    private Boolean occupied;
    @Column(name = "last_updated", nullable = false)
    private LocalDateTime lastUpdated;
    @Version
    @Column(nullable = false)
    private Long version;

    protected ParkingSpace() {}
    public ParkingSpace(String spaceId, String label, Boolean occupied) {
        this.spaceId = spaceId;
        this.label = label;
        this.occupied = occupied;
        this.lastUpdated = LocalDateTime.now();
    }
    public String getSpaceId() { return spaceId; }
    public String getLabel() { return label; }
    public Boolean getOccupied() { return occupied; }
    public LocalDateTime getLastUpdated() { return lastUpdated; }
    public Long getVersion() { return version; }
    public void updateOccupancy(boolean occupied) {
        this.occupied = occupied;
        this.lastUpdated = LocalDateTime.now();
    }
}
