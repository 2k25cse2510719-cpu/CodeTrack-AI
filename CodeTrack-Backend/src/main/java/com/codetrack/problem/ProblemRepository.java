
package com.codetrack.problem;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface ProblemRepository extends JpaRepository<Problem, Long> {

    // Fetch only the current user's problems, newest first
    List<Problem> findAllByUserIdOrderByCreatedAtDesc(Long userId);

    // Find a problem only if it belongs to the specified user
    Optional<Problem> findByIdAndUserId(Long id, Long userId);

    // Delete a problem only if it belongs to the specified user
    void deleteByIdAndUserId(Long id, Long userId);
}
