package edu.lynchburg.terra.dto;

public class ParkingStatusUpdateRequest {
    private String timeStamp;
    private Integer numOfCarsParked;

    public String getTimeStamp() { return timeStamp; }
    public void setTimeStamp(String timeStamp) { this.timeStamp = timeStamp; }

    public Integer getNumOfCarsParked() { return numOfCarsParked; }
    public void setNumOfCarsParked(Integer numOfCarsParked) { this.numOfCarsParked = numOfCarsParked; }
}