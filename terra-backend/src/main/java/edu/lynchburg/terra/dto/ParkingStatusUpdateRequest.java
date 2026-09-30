package edu.lynchburg.terra.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class ParkingStatusUpdateRequest {
    private String timeStamp;
    @NotNull
    @Min(0)
    private Integer numOfCarsParked;

    public String getTimeStamp() { return timeStamp; }
    public void setTimeStamp(String timeStamp) { this.timeStamp = timeStamp; }

    public Integer getNumOfCarsParked() { return numOfCarsParked; }
    public void setNumOfCarsParked(Integer numOfCarsParked) { this.numOfCarsParked = numOfCarsParked; }
}
