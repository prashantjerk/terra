package edu.lynchburg.terra;

import edu.lynchburg.terra.repository.ParkingLogRepository;
import edu.lynchburg.terra.repository.ParkingCheckRepository;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.hamcrest.Matchers.nullValue;

@SpringBootTest(properties="terra.requests-per-minute=1000")
@AutoConfigureMockMvc
class ParkingApiTests {
    @Autowired MockMvc mvc;
    @Autowired ParkingLogRepository logs;
    @Autowired ParkingCheckRepository checks;
    @BeforeEach void reset() { checks.deleteAll(); logs.deleteAll(); }

    @Test void countUpdatesPersistAndReadsReturnOnlyTimestampAndCount() throws Exception {
        mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
            .content("{\"timeStamp\":\"2026-09-30T00:00:00Z\",\"numOfCarsParked\":3}"))
            .andExpect(status().isOk());
        assertEquals(1, logs.count());
        mvc.perform(get("/api/v1/parking/status")).andExpect(status().isOk())
            .andExpect(jsonPath("$.numOfCarsParked").value(3))
            .andExpect(jsonPath("$.timeStamp").exists())
            .andExpect(jsonPath("$.length()").value(2));
    }
    @Test void rejectsNegativeAndMissingCounts() throws Exception {
        for (String body : new String[] {"{\"numOfCarsParked\":-1}", "{}", "{\"numOfCarsParked\":2.5}"}) {
            mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
                .content(body)).andExpect(status().isBadRequest());
        }
        assertEquals(0, logs.count());
    }
    @Test void noObservationDoesNotInventFreshTimestamp() throws Exception {
        mvc.perform(get("/api/v1/parking/status")).andExpect(status().isOk())
            .andExpect(jsonPath("$.timeStamp").value(nullValue()))
            .andExpect(jsonPath("$.numOfCarsParked").value(nullValue()));
    }
    @Test void pollingDoesNotRefreshObservationTimestamp() throws Exception {
        mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
            .content("{\"numOfCarsParked\":2}")).andExpect(status().isOk());
        String first = mvc.perform(get("/api/v1/parking/status"))
            .andReturn().getResponse().getContentAsString();
        String second = mvc.perform(get("/api/v1/parking/status"))
            .andReturn().getResponse().getContentAsString();
        assertEquals(first, second);
        assertEquals(1, logs.count());
    }
    @Test void spaceEndpointIsRemoved() throws Exception {
        mvc.perform(get("/api/v1/parking/spaces")).andExpect(status().isNotFound());
    }
    @Test void repeatedCountUpdatesCheckWithoutAddingHistory() throws Exception {
        for(int count : new int[] {0,0,3,3,11,11}) {
            mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
                .content("{\"numOfCarsParked\":"+count+"}"))
                .andExpect(status().isOk());
        }
        assertEquals(3,logs.count()); assertEquals(1,checks.count());
        mvc.perform(get("/api/v1/parking/status")).andExpect(jsonPath("$.numOfCarsParked").value(11));
    }
    @Test void unconfiguredPiReturnsUnavailableWithoutInventingData() throws Exception {
        mvc.perform(post("/api/v1/parking/refresh")).andExpect(status().isServiceUnavailable())
            .andExpect(header().string("Retry-After","10"));
        assertEquals(0,logs.count()); assertEquals(0,checks.count());
    }

}
