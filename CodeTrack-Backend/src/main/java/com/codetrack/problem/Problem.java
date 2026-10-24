
package com.codetrack.problem;

import com.codetrack.auth.User;
import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "problems")
public class Problem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(length = 100)
    private String platform;

    @Column(length = 30)
    private String difficulty;

    @Column(length = 100)
    private String topic;

    @Column(length = 2048)
    private String url;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ProblemStatus status = ProblemStatus.TODO;

    private LocalDate solvedDate;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    @JsonIgnore
@ManyToOne(fetch = FetchType.LAZY, optional = false)
@JoinColumn(name = "user_id", nullable = false)
private User user;

    public Problem() {}

    @PrePersist
    void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
        if (status == null) {
            status = ProblemStatus.TODO;
        }
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }

    public String getDifficulty() { return difficulty; }
    public void setDifficulty(String difficulty) { this.difficulty = difficulty; }

    public String getTopic() { return topic; }
    public void setTopic(String topic) { this.topic = topic; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public ProblemStatus getStatus() { return status; }
    public void setStatus(ProblemStatus status) { this.status = status; }

    public LocalDate getSolvedDate() { return solvedDate; }
    public void setSolvedDate(LocalDate solvedDate) { this.solvedDate = solvedDate; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
}
