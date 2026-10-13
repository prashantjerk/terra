package edu.lynchburg.terra.controller;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;
import java.util.*;
@Component
public class RequestLimitFilter extends OncePerRequestFilter {
    private record Window(long start, int count) {}
    private final Map<String,Window> windows=new HashMap<>();
    private final int limit;
    public RequestLimitFilter(@Value("${terra.requests-per-minute:5}") int limit) {
        if(limit<1) throw new IllegalArgumentException("Request limit must be positive");
        this.limit=limit;
    }
    private synchronized long retry(String key) {
        long now=System.nanoTime(), minute=60_000_000_000L;
        windows.entrySet().removeIf(e -> now-e.getValue().start()>=minute);
        var w=windows.get(key);
        if(w==null) {
            if(windows.size()>=10000) return 60; // Bound anonymous-client memory.
            windows.put(key,new Window(now,1)); return 0;
        }
        if(w.count()>=limit) return Math.max(1,(minute-(now-w.start())+999_999_999L)/1_000_000_000L);
        windows.put(key,new Window(w.start(),w.count()+1)); return 0;
    }
    @Override protected void doFilterInternal(HttpServletRequest req,HttpServletResponse res,FilterChain chain) throws ServletException,IOException {
        String path=req.getRequestURI();
        if((req.getMethod().equals("GET") && path.equals("/api/v1/parking/status")) ||
           (req.getMethod().equals("POST") && path.equals("/api/v1/parking/refresh"))) {
            long wait=retry(req.getRemoteAddr()); // Never trust client-supplied forwarded headers.
            if(wait>0) {
                res.setStatus(429); res.setHeader("Retry-After",Long.toString(wait));
                res.setHeader("Access-Control-Allow-Origin","http://localhost:3000");
                res.setHeader("Access-Control-Expose-Headers","Retry-After");
                res.setContentType("application/json"); res.getWriter().write("{\"error\":\"Too many requests\"}"); return;
            }
        }
        chain.doFilter(req,res);
    }
}
