package edu.lynchburg.terra;
import com.sun.net.httpserver.HttpServer;
import edu.lynchburg.terra.repository.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
@SpringBootTest(properties={"terra.cache-seconds=1","terra.requests-per-minute=1000"})
@AutoConfigureMockMvc
class OnDemandApiTests {
    private static final AtomicInteger calls=new AtomicInteger();
    private static final AtomicInteger count=new AtomicInteger(7);
    private static final HttpServer pi;
    static {
        try {
            pi=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
            pi.createContext("/detect",exchange -> {
                calls.incrementAndGet();
                boolean authorized="Bearer integration-token".equals(exchange.getRequestHeaders().getFirst("Authorization"));
                int status=!authorized?401:count.get()<0?503:200;
                byte[] body=("{\"timeStamp\":\"2026-10-12T20:00:00Z\",\"numOfCarsParked\":"+Math.max(0,count.get())+"}").getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type","application/json");
                exchange.sendResponseHeaders(status,body.length);
                exchange.getResponseBody().write(body); exchange.close();
            });
            pi.start();
        } catch(Exception e) { throw new ExceptionInInitializerError(e); }
    }
    @DynamicPropertySource static void properties(DynamicPropertyRegistry registry) {
        registry.add("terra.pi-url",() -> "http://127.0.0.1:"+pi.getAddress().getPort()+"/detect");
        registry.add("terra.pi-token",() -> "integration-token");
    }
    @Autowired MockMvc mvc;
    @Autowired ParkingLogRepository logs;
    @Autowired ParkingCheckRepository checks;
    @AfterAll static void stop() { pi.stop(0); }
    @Test void realHttpDetectionCachesDeduplicatesAndRetainsStatusOnFailure() throws Exception {
        checks.deleteAll(); logs.deleteAll();
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isOk())
            .andExpect(jsonPath("$.numOfCarsParked").value(7)).andExpect(jsonPath("$.length()").value(2));
        var first=checks.findById(1L).orElseThrow().getCheckedAt();
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isOk());
        assertEquals(1,calls.get()); assertEquals(1,logs.count());
        Thread.sleep(1100);
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isOk());
        assertEquals(2,calls.get()); assertEquals(1,logs.count());
        assertTrue(checks.findById(1L).orElseThrow().getCheckedAt().isAfter(first));
        count.set(0); Thread.sleep(1100);
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isOk())
            .andExpect(jsonPath("$.numOfCarsParked").value(0));
        assertEquals(2,logs.count());
        count.set(-1); Thread.sleep(1100);
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isServiceUnavailable());
        mvc.perform(get("/api/v1/parking/status")).andExpect(status().isOk())
            .andExpect(jsonPath("$.numOfCarsParked").value(0));
        assertEquals(2,logs.count());
    }
}
