package edu.lynchburg.terra;
import edu.lynchburg.terra.service.*;
import edu.lynchburg.terra.dto.*;
import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
class RefreshServiceTests {
    @Test void concurrentUsersShareOneDetectionAndCachedResult() throws Exception {
        var parking=mock(ParkingService.class); var pi=mock(PiClient.class);
        var entered=new CountDownLatch(1); var release=new CountDownLatch(1);
        var request=new ParkingStatusUpdateRequest(); request.setNumOfCarsParked(7);
        var result=new ParkingSummaryResponse(LocalDateTime.now(),7);
        when(pi.detect()).thenAnswer(call -> { entered.countDown(); assertTrue(release.await(5,TimeUnit.SECONDS)); return request; });
        when(parking.getLatestStatus()).thenReturn(result);
        var service=new RefreshService(parking,pi,30);
        var pool=Executors.newFixedThreadPool(2);
        try {
            var first=pool.submit(service::refresh);
            assertTrue(entered.await(5,TimeUnit.SECONDS));
            var second=pool.submit(service::refresh);
            release.countDown();
            assertSame(result,first.get(5,TimeUnit.SECONDS));
            assertSame(result,second.get(5,TimeUnit.SECONDS));
            assertSame(result,service.refresh());
            verify(pi,times(1)).detect(); verify(parking,times(1)).updateParkingStatus(request);
        } finally { release.countDown(); pool.shutdownNow(); }
    }
    @Test void failureDoesNotSaveOrImmediatelyRetry() {
        var parking=mock(ParkingService.class); var pi=mock(PiClient.class);
        when(pi.detect()).thenThrow(new IllegalStateException("offline"));
        var service=new RefreshService(parking,pi,30);
        assertThrows(RuntimeException.class, service::refresh);
        assertThrows(RuntimeException.class, service::refresh);
        verify(pi,times(1)).detect(); verifyNoInteractions(parking);
    }
}
