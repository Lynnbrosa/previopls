package com.previopls.config;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.assertj.core.api.Assertions.assertThat;

class RateLimitFilterTest {

    private static MockHttpServletRequest login(String ip) {
        MockHttpServletRequest req = new MockHttpServletRequest("POST", "/v1/auth/login");
        req.setRemoteAddr(ip);
        return req;
    }

    @Test
    void limiteDeLoginEhPorIpENaoGlobal() throws Exception {
        RateLimitFilter filter = new RateLimitFilter(2, 200);

        MockHttpServletResponse r1 = new MockHttpServletResponse();
        MockHttpServletResponse r2 = new MockHttpServletResponse();
        MockHttpServletResponse r3 = new MockHttpServletResponse();
        filter.doFilter(login("10.0.0.1"), r1, new MockFilterChain());
        filter.doFilter(login("10.0.0.1"), r2, new MockFilterChain());
        filter.doFilter(login("10.0.0.1"), r3, new MockFilterChain());
        assertThat(r1.getStatus()).isEqualTo(200);
        assertThat(r2.getStatus()).isEqualTo(200);
        assertThat(r3.getStatus()).isEqualTo(429); // terceiro do MESMO ip estoura o limite 2/min

        MockHttpServletResponse outro = new MockHttpServletResponse();
        filter.doFilter(login("10.0.0.2"), outro, new MockFilterChain());
        assertThat(outro.getStatus()).isEqualTo(200); // outro ip tem o proprio bucket
    }

    @Test
    void usaPrimeiroIpDoXForwardedForQuandoAtrasDeProxy() throws Exception {
        RateLimitFilter filter = new RateLimitFilter(1, 200);

        MockHttpServletRequest a = login("172.18.0.5");
        a.addHeader("X-Forwarded-For", "203.0.113.7, 172.18.0.2");
        MockHttpServletRequest b = login("172.18.0.5");
        b.addHeader("X-Forwarded-For", "203.0.113.8, 172.18.0.2");

        MockHttpServletResponse ra = new MockHttpServletResponse();
        MockHttpServletResponse rb = new MockHttpServletResponse();
        filter.doFilter(a, ra, new MockFilterChain());
        filter.doFilter(b, rb, new MockFilterChain());
        assertThat(ra.getStatus()).isEqualTo(200);
        assertThat(rb.getStatus()).isEqualTo(200); // ips de origem diferentes, buckets diferentes
    }

    @Test
    void healthEVersionNaoContam() throws Exception {
        RateLimitFilter filter = new RateLimitFilter(1, 1);
        for (int i = 0; i < 5; i++) {
            MockHttpServletRequest req = new MockHttpServletRequest("GET", "/health");
            req.setRemoteAddr("10.0.0.9");
            MockHttpServletResponse res = new MockHttpServletResponse();
            filter.doFilter(req, res, new MockFilterChain());
            assertThat(res.getStatus()).isEqualTo(200);
        }
    }
}
