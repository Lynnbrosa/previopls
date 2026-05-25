package com.previopls.controller;

import com.previopls.dto.cliente.ClienteCreateRequest;
import com.previopls.dto.cliente.ClienteCreatedResponse;
import com.previopls.service.ClienteService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v1/clientes")
@Tag(name = "clientes", description = "Cadastro D0 da compra — dispara classificação")
public class ClienteController {

    private final ClienteService clienteService;

    public ClienteController(ClienteService clienteService) {
        this.clienteService = clienteService;
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Cadastra cliente D0 da compra e dispara classificação preditiva")
    public ResponseEntity<ClienteCreatedResponse> cadastrar(@Valid @RequestBody ClienteCreateRequest request) {
        ClienteCreatedResponse response = clienteService.cadastrarCompra(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
