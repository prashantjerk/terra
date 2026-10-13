package edu.lynchburg.terra.service;
import edu.lynchburg.terra.dto.*;
import edu.lynchburg.terra.model.*;
import edu.lynchburg.terra.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import java.time.LocalDateTime;
@Service
public class ParkingService {
    private final ParkingLogRepository logs;
    private final ParkingCheckRepository checks;
    private final TransactionTemplate transaction;
    public ParkingService(ParkingLogRepository logs, ParkingCheckRepository checks, PlatformTransactionManager manager) { this.logs=logs; this.checks=checks; this.transaction=new TransactionTemplate(manager); }
    public ParkingSummaryResponse getLatestStatus() {
        return checks.findById(1L).map(c -> new ParkingSummaryResponse(c.getCheckedAt(),c.getCount()))
            .orElseGet(() -> logs.findTopByOrderByRecordedAtDescIdDesc()
                .map(l -> new ParkingSummaryResponse(l.getRecordedAt(),l.getNumCarsParked()))
                .orElse(new ParkingSummaryResponse(null,null)));
    }
    public synchronized void updateParkingStatus(ParkingStatusUpdateRequest request) {
        Integer count=request.getNumOfCarsParked();
        if (count==null || count<0) throw new IllegalArgumentException("Invalid count");
        transaction.executeWithoutResult(status -> {
        Integer previous=getLatestStatus().getNumOfCarsParked();
        if (!count.equals(previous)) logs.save(new ParkingLog(count));
        // One durable current-state row, including successful unchanged checks.
        checks.save(new ParkingCheck(count, LocalDateTime.now()));
        });
    }
}
