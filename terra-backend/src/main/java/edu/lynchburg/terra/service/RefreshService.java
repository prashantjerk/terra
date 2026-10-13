package edu.lynchburg.terra.service;
import edu.lynchburg.terra.dto.ParkingSummaryResponse;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import java.util.concurrent.*;
@Service
public class RefreshService {
    private final ParkingService parking;
    private final PiClient pi;
    private final long ttl;
    private ParkingSummaryResponse cached;
    private long expires;
    private long retryAt;
    private CompletableFuture<ParkingSummaryResponse> pending;
    public RefreshService(ParkingService parking, PiClient pi, @Value("${terra.cache-seconds:30}") long seconds) {
        if (seconds<1) throw new IllegalArgumentException("Cache TTL must be positive");
        this.parking=parking; this.pi=pi; ttl=TimeUnit.SECONDS.toNanos(seconds);
    }
    public ParkingSummaryResponse refresh() {
        CompletableFuture<ParkingSummaryResponse> job;
        boolean owner;
        synchronized(this) {
            if (cached!=null && System.nanoTime()<expires) return cached;
            if (pending==null && System.nanoTime()<retryAt) throw new IllegalStateException("Pi retry cooldown");
            owner=pending==null;
            if(owner) pending=new CompletableFuture<>();
            job=pending;
        }
        if(owner) {
            try {
                parking.updateParkingStatus(pi.detect());
                var result=parking.getLatestStatus();
                synchronized(this) { cached=result; expires=System.nanoTime()+ttl; }
                job.complete(result);
            } catch(Exception e) {
                synchronized(this) { retryAt=System.nanoTime()+TimeUnit.SECONDS.toNanos(10); }
                job.completeExceptionally(e);
            }
            finally { synchronized(this) { pending=null; } }
        }
        return job.join();
    }
}
