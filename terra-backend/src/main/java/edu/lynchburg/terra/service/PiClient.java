package edu.lynchburg.terra.service;
import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
import edu.lynchburg.terra.dto.ParkingPhotoResult;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import java.net.http.HttpClient;
import java.time.Duration;
@Component
public class PiClient {
    private final String url, token;
    private final RestClient client;
    public PiClient(@Value("${terra.pi-url:}") String url, @Value("${terra.pi-token:}") String token,
                    @Value("${terra.pi-timeout-seconds:60}") int timeout) {
        this.url=url; this.token=token;
        var factory=new JdkClientHttpRequestFactory(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build());
        factory.setReadTimeout(Duration.ofSeconds(timeout));
        client=RestClient.builder().requestFactory(factory).build();
    }
    public String[] listPhotos(String photoUrl) {
        return client.get().uri(photoUrl).header("Authorization", authorization())
            .retrieve().body(String[].class);
    }

    public ParkingPhotoResult checkPhoto(String photoUrl, String name) {
        return client.post().uri(photoUrl).header("Authorization", authorization())
            .contentType(MediaType.APPLICATION_JSON).body(Map.of("photo", name))
            .retrieve().body(ParkingPhotoResult.class);
    }

    private String authorization() {
        if (token.isBlank()) throw new IllegalStateException("Pi token not configured");
        return "Bearer " + token;
    }

    public ParkingStatusUpdateRequest detect() {
        if (url.isBlank() || token.isBlank()) throw new IllegalStateException("Pi URL/token not configured");
        var result=client.post().uri(url).header("Authorization","Bearer "+token)
            .retrieve().body(ParkingStatusUpdateRequest.class);
        if (result==null || result.getNumOfCarsParked()==null || result.getNumOfCarsParked()<0)
            throw new IllegalStateException("Pi returned invalid count");
        return result;
    }
}
