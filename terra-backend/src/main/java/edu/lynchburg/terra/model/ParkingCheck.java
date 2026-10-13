package edu.lynchburg.terra.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity
@Table(name="parking_latest_check")
public class ParkingCheck {
    @Id private Long id = 1L;
    @Column(name="num_cars_parked", nullable=false) private Integer count;
    @Column(name="checked_at", nullable=false) private LocalDateTime checkedAt;
    public ParkingCheck() {}
    public ParkingCheck(Integer count, LocalDateTime checkedAt) { this.count=count; this.checkedAt=checkedAt; }
    public Integer getCount() { return count; }
    public LocalDateTime getCheckedAt() { return checkedAt; }
}
