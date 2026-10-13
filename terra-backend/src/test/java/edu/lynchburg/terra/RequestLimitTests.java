package edu.lynchburg.terra;
import edu.lynchburg.terra.controller.RequestLimitFilter;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.*;
import static org.junit.jupiter.api.Assertions.*;
class RequestLimitTests {
    @Test void sixthRequestIsRejectedAndOtherClientIsIndependent() throws Exception {
        var filter=new RequestLimitFilter(5);
        for(int i=0;i<6;i++) {
            var req=new MockHttpServletRequest("POST","/api/v1/parking/refresh");
            req.setRemoteAddr("192.168.1.1");
            var res=new MockHttpServletResponse();
            filter.doFilter(req,res,new MockFilterChain());
            assertEquals(i<5?200:429,res.getStatus());
            if(i==5) assertNotNull(res.getHeader("Retry-After"));
        }
        var req=new MockHttpServletRequest("POST","/api/v1/parking/refresh");
        req.setRemoteAddr("192.168.1.2");
        var res=new MockHttpServletResponse();
        filter.doFilter(req,res,new MockFilterChain()); assertEquals(200,res.getStatus());
    }
}
