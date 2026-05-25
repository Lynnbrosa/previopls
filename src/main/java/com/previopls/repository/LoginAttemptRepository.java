package com.previopls.repository;

import com.previopls.entity.LoginAttempt;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.UUID;

@Repository
public interface LoginAttemptRepository extends JpaRepository<LoginAttempt, UUID> {

    @Query("""
            SELECT count(la) FROM LoginAttempt la
            WHERE la.email = :email
              AND la.success = false
              AND la.attemptedAt >= :since
            """)
    long countFailuresSince(@Param("email") String email, @Param("since") Instant since);
}
