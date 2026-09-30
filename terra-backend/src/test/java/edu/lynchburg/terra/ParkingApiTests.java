package edu.lynchburg.terra;

import edu.lynchburg.terra.repository.*;
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

@SpringBootTest
@AutoConfigureMockMvc
class ParkingApiTests {
    @Autowired MockMvc mvc;
    @Autowired ParkingSpaceRepository spaces;
    @Autowired ParkingLogRepository logs;
    private static final String BASE = "/api/v1/parking/spaces";

    @BeforeEach void reset() { spaces.deleteAll(); logs.deleteAll(); }
    private void create(String id, String occupancy) throws Exception {
        mvc.perform(post(BASE).contentType(MediaType.APPLICATION_JSON)
            .content("{\"spaceId\":\"" + id + "\",\"label\":\"Row A\",\"occupied\":" + occupancy + "}"))
            .andExpect(status().isCreated()).andExpect(header().string("Location", BASE + "/" + id));
    }
    @Test void createsAndPersistsUnknownSpace() throws Exception {
        create("A1", "null");
        assertNull(spaces.findById("A1").orElseThrow().getOccupied());
        mvc.perform(get(BASE + "/A1")).andExpect(status().isOk())
            .andExpect(jsonPath("$.spaceId").value("A1"))
            .andExpect(jsonPath("$.occupied").value(nullValue()))
            .andExpect(jsonPath("$.lastUpdated").exists());
    }
    @Test void updatesAndSummarizesUnknownSeparately() throws Exception {
        create("A1", "null"); create("A2", "false"); create("A3", "null");
        mvc.perform(put(BASE + "/A1/status").contentType(MediaType.APPLICATION_JSON)
            .content("{\"occupied\":true}"))
            .andExpect(status().isOk()).andExpect(jsonPath("$.occupied").value(true));
        assertTrue(spaces.findById("A1").orElseThrow().getOccupied());
        mvc.perform(get(BASE + "/summary")).andExpect(status().isOk())
            .andExpect(jsonPath("$.totalSpaces").value(3))
            .andExpect(jsonPath("$.occupiedSpaces").value(1))
            .andExpect(jsonPath("$.availableSpaces").value(1))
            .andExpect(jsonPath("$.unknownSpaces").value(1));
    }
    @Test void listsSpacesInIdOrder() throws Exception {
        create("B2", "true"); create("A1", "false");
        mvc.perform(get(BASE)).andExpect(status().isOk())
            .andExpect(jsonPath("$[0].spaceId").value("A1"))
            .andExpect(jsonPath("$[1].spaceId").value("B2"));
    }
    @Test void duplicateIsConflictWithoutOverwrite() throws Exception {
        create("A1", "true");
        mvc.perform(post(BASE).contentType(MediaType.APPLICATION_JSON)
            .content("{\"spaceId\":\"A1\",\"label\":\"Replacement\",\"occupied\":false}"))
            .andExpect(status().isConflict());
        assertTrue(spaces.findById("A1").orElseThrow().getOccupied());
    }
    @Test void missingSpaceReturns404() throws Exception {
        mvc.perform(get(BASE + "/missing")).andExpect(status().isNotFound());
        mvc.perform(put(BASE + "/missing/status").contentType(MediaType.APPLICATION_JSON)
            .content("{\"occupied\":false}")).andExpect(status().isNotFound());
    }
    @Test void invalidInputsReturn400() throws Exception {
        for (String body : new String[] {
            "{\"spaceId\":\"bad/id\",\"label\":\"A\"}",
            "{\"spaceId\":\"A1\",\"label\":\" \"}",
            "{\"spaceId\":\"summary\",\"label\":\"A\"}"}) {
            mvc.perform(post(BASE).contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest());
        }
        assertEquals(0, spaces.count());
        create("A1", "false");
        mvc.perform(put(BASE + "/A1/status").contentType(MediaType.APPLICATION_JSON)
            .content("{}")).andExpect(status().isBadRequest());
        assertFalse(spaces.findById("A1").orElseThrow().getOccupied());
    }
    @Test void aggregateEndpointsRemainCompatible() throws Exception {
        mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
            .content("{\"timeStamp\":\"2026-09-30T00:00:00Z\",\"numOfCarsParked\":3}"))
            .andExpect(status().isOk());
        assertEquals(1, logs.count());
        mvc.perform(get("/api/v1/parking/status")).andExpect(status().isOk())
            .andExpect(jsonPath("$.numOfCarsParked").value(3))
            .andExpect(jsonPath("$.timeStamp").exists());
    }
    @Test void rejectsNegativeAndMissingCounts() throws Exception {
        for (String body : new String[] {"{\"numOfCarsParked\":-1}", "{}"}) {
            mvc.perform(post("/api/v1/parking/update").contentType(MediaType.APPLICATION_JSON)
                .content(body)).andExpect(status().isBadRequest());
        }
        assertEquals(0, logs.count());
    }
}
