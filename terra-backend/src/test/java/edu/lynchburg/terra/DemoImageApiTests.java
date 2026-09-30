package edu.lynchburg.terra;

import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.nio.file.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class DemoImageApiTests {
    @Autowired MockMvc mvc;
    private static final Path IMAGE = createTempImage();
    private static Path createTempImage() {
        try { return Files.createTempFile("terra-demo-test", ".jpg"); }
        catch (Exception exception) { throw new RuntimeException(exception); }
    }
    @DynamicPropertySource static void configure(DynamicPropertyRegistry registry) {
        registry.add("terra.demo-image", () -> IMAGE.toString());
    }
    @BeforeEach void writeImage() throws Exception {
        ImageIO.write(new BufferedImage(2, 2, BufferedImage.TYPE_INT_RGB), "jpg", IMAGE.toFile());
    }
    @AfterAll static void cleanup() throws Exception { Files.deleteIfExists(IMAGE); }
    @Test void servesConfiguredPhotoWithoutCaching() throws Exception {
        mvc.perform(get("/api/v1/parking/demo-image"))
            .andExpect(status().isOk()).andExpect(content().contentType("image/jpeg"))
            .andExpect(header().string("Cache-Control", "no-store"))
            .andExpect(content().bytes(Files.readAllBytes(IMAGE)));
    }
    @Test void missingImageReturns404() throws Exception {
        Files.delete(IMAGE);
        mvc.perform(get("/api/v1/parking/demo-image")).andExpect(status().isNotFound());
    }
}
