package edu.lynchburg.terra.dto;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.stream.IntStream;

public record ParkingPhotoResult(String photo, OffsetDateTime checkedAt, int capacity, int occupied,
                              int available, Map<String, String> spaces, String previewJpeg) {
        public boolean validFor(String name) {
            return name.equals(photo) && checkedAt != null && capacity == 9 && spaces != null
                && spaces.size() == capacity && IntStream.rangeClosed(1, capacity)
                    .allMatch(i -> {
                        String state = spaces.get("P%02d".formatted(i));
                        return "occupied".equals(state) || "available".equals(state);
                    })
                && occupied == spaces.values().stream().filter("occupied"::equals).count()
                && available == capacity - occupied
                && previewJpeg != null && !previewJpeg.isBlank() && previewJpeg.length() <= 2_666_668;
        }
    }
