package edu.lynchburg.terra.service;
import edu.lynchburg.terra.dto.ParkingStatusUpdateRequest;
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
    public ParkingStatusUpdateRequest detect() {
        if (url.isBlank() || token.isBlank()) throw new IllegalStateException("Pi URL/token not configured");
        var result=client.post().uri(url).header("Authorization","Bearer "+token)
            .retrieve().body(ParkingStatusUpdateRequest.class);
        if (result==null || result.getNumOfCarsParked()==null || result.getNumOfCarsParked()<0)
            throw new IllegalStateException("Pi returned invalid count");
        return result;
    }
}
