package com.previopls.repository;

import com.previopls.entity.Lead;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface LeadRepository extends JpaRepository<Lead, UUID> {

    @Query("""
            SELECT l FROM Lead l
            LEFT JOIN FETCH l.cliente
            LEFT JOIN FETCH l.veiculo
            WHERE l.id = :id
            """)
    Optional<Lead> findByIdWithDetails(@Param("id") UUID id);

    @Query(value = """
            SELECT l FROM Lead l
            JOIN FETCH l.cliente
            JOIN FETCH l.veiculo
            WHERE (:prioridade IS NULL OR l.prioridade = :prioridade)
              AND (:status IS NULL OR l.status = :status)
            ORDER BY
              CASE l.prioridade
                WHEN com.previopls.entity.enums.PrioridadeLead.CRITICA THEN 0
                WHEN com.previopls.entity.enums.PrioridadeLead.ALTA THEN 1
                WHEN com.previopls.entity.enums.PrioridadeLead.MEDIA THEN 2
                ELSE 3
              END ASC,
              l.scoreRisco DESC,
              l.criadoEm DESC
            """,
            countQuery = """
                    SELECT count(l) FROM Lead l
                    WHERE (:prioridade IS NULL OR l.prioridade = :prioridade)
                      AND (:status IS NULL OR l.status = :status)
                    """)
    Page<Lead> findFiltered(
            @Param("prioridade") PrioridadeLead prioridade,
            @Param("status") StatusLead status,
            Pageable pageable);
}
