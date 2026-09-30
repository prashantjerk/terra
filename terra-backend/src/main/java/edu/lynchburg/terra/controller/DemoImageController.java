package edu.lynchburg.terra.controller;

import java.nio.file.Files;
import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

/** Serves a single configured demo photo; never accepts arbitrary paths or uploads. */
@RestController
@RequestMapping("/api/v1/parking")
@CrossOrigin(origins = "http://localhost:3000")
public class DemoImageController {
    private final Path image;
    public DemoImageController(@Value("${terra.demo-image:../parkinglot/WIN_20260929_14_58_01_Pro.jpg}") String image) {
        this.image = Path.of(image).toAbsolutePath().normalize();
    }
    @GetMapping("/demo-image")
    public ResponseEntity<Resource> image() {
        if (!Files.isRegularFile(image) || !Files.isReadable(image)) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok().contentType(MediaType.IMAGE_JPEG)
            .cacheControl(CacheControl.noStore()).body(new FileSystemResource(image));
    }
}
