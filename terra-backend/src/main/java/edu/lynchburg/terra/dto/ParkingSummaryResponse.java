package edu.lynchburg.terra.dto;

import java.time.LocalDateTime;

public class ParkingSummaryResponse {
    private LocalDateTime timeStamp;
    private Integer numOfCarsParked;

    public ParkingSummaryResponse(LocalDateTime timeStamp, Integer numOfCarsParked) {
        this.timeStamp = timeStamp;
        this.numOfCarsParked = numOfCarsParked;
    }

    public LocalDateTime getTimeStamp() { return timeStamp; }
    public void setTimeStamp(LocalDateTime timeStamp) { this.timeStamp = timeStamp; }

    public Integer getNumOfCarsParked() { return numOfCarsParked; }
    public void setNumOfCarsParked(Integer numOfCarsParked) { this.numOfCarsParked = numOfCarsParked; }
}