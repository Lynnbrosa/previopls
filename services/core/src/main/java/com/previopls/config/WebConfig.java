package com.previopls.config;

import com.previopls.entity.enums.PerfilCliente;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.RolePapel;
import com.previopls.entity.enums.StatusLead;
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(String.class, PrioridadeLead.class, PrioridadeLead::fromValue);
        registry.addConverter(String.class, StatusLead.class, StatusLead::fromValue);
        registry.addConverter(String.class, PerfilCliente.class, PerfilCliente::fromValue);
        registry.addConverter(String.class, RolePapel.class, RolePapel::fromValue);
    }
}
