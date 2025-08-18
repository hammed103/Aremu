# 📊 Aremu System Flow Diagrams

## 🎯 Overview

This document contains comprehensive flow diagrams for the Aremu Intelligent WhatsApp Job Distribution System.

## 🔄 Complete System Architecture

```mermaid
graph TB
    subgraph "External Sources"
        LS[LinkedIn Jobs]
        IS[Indeed Jobs]
        JS[JobSpy Sources]
    end
    
    subgraph "Data Collection Layer"
        LSC[LinkedIn Scraper]
        JSC[JobSpy Scraper]
        RJT[Raw Jobs Table]
    end
    
    subgraph "AI Processing Layer"
        AIP[AI Enhanced Parser]
        OAI[OpenAI GPT-4]
        CJT[Canonical Jobs Table]
    end
    
    subgraph "Smart Delivery Layer"
        SDE[Smart Delivery Engine]
        IJM[Intelligent Job Matcher]
        JTS[Job Tracking System]
    end
    
    subgraph "WhatsApp Bot Layer"
        WBA[WhatsApp Bot App]
        FPM[Flexible Preference Manager]
        WMS[Window Management System]
    end
    
    subgraph "Database Layer"
        PG[(PostgreSQL)]
        UT[Users Table]
        UPT[User Preferences Table]
        JHT[Job History Table]
        CWT[Conversation Windows Table]
    end
    
    subgraph "User Interface"
        WU[WhatsApp Users]
    end
    
    LS --> LSC
    IS --> JSC
    JS --> JSC
    LSC --> RJT
    JSC --> RJT
    
    RJT --> AIP
    AIP --> OAI
    OAI --> AIP
    AIP --> CJT
    
    CJT --> SDE
    SDE --> IJM
    IJM --> JTS
    
    SDE --> WBA
    WBA --> FPM
    WBA --> WMS
    
    FPM --> UPT
    WMS --> CWT
    JTS --> JHT
    WBA --> UT
    
    UT --> PG
    UPT --> PG
    JHT --> PG
    CWT --> PG
    CJT --> PG
    RJT --> PG
    
    WBA --> WU
    WU --> WBA
    
    style LS fill:#e1f5fe
    style IS fill:#e1f5fe
    style JS fill:#e1f5fe
    style OAI fill:#fff3e0
    style WU fill:#e8f5e8
    style PG fill:#f3e5f5
```

## ⚡ Real-Time Job Distribution Flow

```mermaid
sequenceDiagram
    participant JS as Job Source
    participant SC as Scraper
    participant DP as Data Parser
    participant AI as OpenAI
    participant SD as Smart Delivery
    participant DB as Database
    participant WB as WhatsApp Bot
    participant U as User
    
    Note over JS,U: Real-Time Job Distribution Pipeline
    
    JS->>SC: New job posted
    SC->>DP: Raw job data
    DP->>AI: Enhance job data
    AI->>DP: Enhanced job info
    DP->>DB: Save canonical job
    DP->>SD: Trigger delivery check
    
    SD->>DB: Get eligible users
    DB->>SD: Active users list
    SD->>SD: Calculate match scores
    
    alt Match Score ≥ 39%
        SD->>WB: Send job alert
        WB->>U: 🚨 NEW JOB ALERT!
        WB->>DB: Mark job as shown
    else Match Score < 39%
        SD->>SD: Skip delivery
    end
    
    Note over SD,U: Average delivery time: <2 seconds
```

## 📱 User Interaction Flow

```mermaid
stateDiagram-v2
    [*] --> NewUser: First message
    NewUser --> PreferenceExtraction: Extract job preferences
    PreferenceExtraction --> PreferenceExtraction: Gather more info
    PreferenceExtraction --> ConfirmationPending: Enough preferences
    ConfirmationPending --> JobDelivery: User confirms
    ConfirmationPending --> PreferenceExtraction: User modifies
    JobDelivery --> ActiveMonitoring: Jobs sent
    ActiveMonitoring --> ActiveMonitoring: Real-time alerts
    ActiveMonitoring --> FourHourReminder: 20 hours elapsed
    FourHourReminder --> BatteryWarning: 23 hours elapsed
    BatteryWarning --> WindowExpired: 24 hours elapsed
    WindowExpired --> NewUser: User returns
    
    ActiveMonitoring --> ActiveMonitoring: User activity resets window
    FourHourReminder --> ActiveMonitoring: User activity resets window
    BatteryWarning --> ActiveMonitoring: User activity resets window
```

## 🧠 Intelligent Matching Algorithm

```mermaid
flowchart TD
    Start([New Job Available]) --> GetUsers[Get Eligible Users]
    GetUsers --> UserLoop{For Each User}
    
    UserLoop --> CheckDaily{Daily Limit OK?}
    CheckDaily -->|No| NextUser[Next User]
    CheckDaily -->|Yes| CheckWindow{Active Window?}
    CheckWindow -->|No| NextUser
    CheckWindow -->|Yes| CheckSeen{Job Already Shown?}
    CheckSeen -->|Yes| NextUser
    CheckSeen -->|No| CalcScore[Calculate Match Score]
    
    CalcScore --> TitleScore[AI Job Titles Match: 35%]
    CalcScore --> SkillsScore[Skills Match: 25%]
    CalcScore --> LocationScore[Location Match: 20%]
    CalcScore --> SalaryScore[Salary Match: 10%]
    CalcScore --> ExperienceScore[Experience Match: 10%]
    
    TitleScore --> CombineScores[Combine Weighted Scores]
    SkillsScore --> CombineScores
    LocationScore --> CombineScores
    SalaryScore --> CombineScores
    ExperienceScore --> CombineScores
    
    CombineScores --> CheckThreshold{Score ≥ 39%?}
    CheckThreshold -->|No| NextUser
    CheckThreshold -->|Yes| SendAlert[Send WhatsApp Alert]
    SendAlert --> MarkShown[Mark Job as Shown]
    MarkShown --> NextUser
    
    NextUser --> UserLoop
    UserLoop -->|All Users Processed| End([Complete])
    
    style Start fill:#e8f5e8
    style End fill:#ffebee
    style SendAlert fill:#fff3e0
    style CheckThreshold fill:#e1f5fe
```

## 🔋 Window Management Lifecycle

```mermaid
gantt
    title 24-Hour WhatsApp Window Management
    dateFormat X
    axisFormat %H:%M
    
    section Active Phase
    Job Delivery Active     :active, phase1, 0, 20h
    Real-time Monitoring   :active, monitor, 0, 20h
    
    section Warning Phase
    4-Hour Reminder        :crit, reminder, 20h, 3h
    Battery Warning        :crit, battery, 23h, 1h
    
    section Sleep Phase
    Window Expired         :done, expired, 24h, 24h
    
    section Reset Events
    User Message Resets    :milestone, reset1, 5h, 0
    User Message Resets    :milestone, reset2, 12h, 0
    User Message Resets    :milestone, reset3, 18h, 0
```

## 📊 Database Relationship Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        varchar phone_number UK
        varchar name
        timestamp created_at
        timestamp last_active
        boolean is_active
    }
    
    USER_PREFERENCES {
        int id PK
        int user_id FK
        text[] job_roles
        text[] job_categories
        text[] preferred_locations
        text[] technical_skills
        int years_of_experience
        int salary_min
        varchar salary_currency
        text[] work_arrangements
        boolean preferences_confirmed
        timestamp created_at
        timestamp updated_at
    }
    
    CANONICAL_JOBS {
        int id PK
        varchar title
        varchar company
        varchar location
        int salary_min
        int salary_max
        varchar salary_currency
        varchar employment_type
        date posted_date
        text job_url
        text description
        boolean ai_enhanced
        text[] ai_job_titles
        text[] ai_skills
        text ai_industry
        text ai_summary
        varchar source
        varchar source_job_id
        timestamp scraped_at
        timestamp created_at
    }
    
    USER_JOB_HISTORY {
        int id PK
        int user_id FK
        int job_id FK
        timestamp shown_at
        float match_score
        varchar delivery_type
        boolean message_sent
    }
    
    CONVERSATION_WINDOWS {
        int id PK
        int user_id FK
        timestamp window_start
        timestamp last_activity
        varchar window_status
        boolean battery_warning_sent
        boolean four_hour_reminder_sent
        int messages_in_window
    }
    
    USERS ||--|| USER_PREFERENCES : has
    USERS ||--o{ USER_JOB_HISTORY : receives
    USERS ||--o{ CONVERSATION_WINDOWS : maintains
    CANONICAL_JOBS ||--o{ USER_JOB_HISTORY : tracked_in
```

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
        SSL[SSL Termination]
    end
    
    subgraph "Application Tier"
        WB1[WhatsApp Bot Instance 1]
        WB2[WhatsApp Bot Instance 2]
        DP[Data Parser Service]
    end
    
    subgraph "Data Tier"
        PG[(PostgreSQL Primary)]
        PGR[(PostgreSQL Replica)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "External Services"
        WA[WhatsApp Business API]
        OAI[OpenAI API]
        JS[Job Sources]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[AlertManager]
    end
    
    Internet --> LB
    LB --> SSL
    SSL --> WB1
    SSL --> WB2
    
    WB1 --> PG
    WB2 --> PG
    DP --> PG
    
    WB1 --> REDIS
    WB2 --> REDIS
    
    PG --> PGR
    
    WB1 --> WA
    WB2 --> WA
    DP --> OAI
    DP --> JS
    
    WB1 --> PROM
    WB2 --> PROM
    DP --> PROM
    PG --> PROM
    
    PROM --> GRAF
    PROM --> ALERT
    
    style LB fill:#e1f5fe
    style PG fill:#f3e5f5
    style WA fill:#e8f5e8
    style OAI fill:#fff3e0
```

## 📈 Performance Monitoring Flow

```mermaid
flowchart LR
    subgraph "Metrics Collection"
        APP[Application Metrics]
        SYS[System Metrics]
        BIZ[Business Metrics]
    end
    
    subgraph "Processing"
        PROM[Prometheus]
        AGG[Aggregation Rules]
    end
    
    subgraph "Visualization"
        GRAF[Grafana Dashboards]
        ALERT[Alert Rules]
    end
    
    subgraph "Notifications"
        EMAIL[Email Alerts]
        SLACK[Slack Notifications]
        SMS[SMS Alerts]
    end
    
    APP --> PROM
    SYS --> PROM
    BIZ --> PROM
    
    PROM --> AGG
    AGG --> GRAF
    AGG --> ALERT
    
    ALERT --> EMAIL
    ALERT --> SLACK
    ALERT --> SMS
    
    style PROM fill:#e1f5fe
    style GRAF fill:#e8f5e8
    style ALERT fill:#ffebee
```

## 🔄 CI/CD Pipeline Flow

```mermaid
flowchart TD
    DEV[Developer Push] --> GIT[Git Repository]
    GIT --> TRIGGER[GitHub Actions Trigger]
    
    TRIGGER --> TEST[Run Tests]
    TEST --> BUILD[Build Application]
    BUILD --> SECURITY[Security Scan]
    SECURITY --> DEPLOY[Deploy to Staging]
    
    DEPLOY --> SMOKE[Smoke Tests]
    SMOKE --> APPROVE{Manual Approval}
    
    APPROVE -->|Approved| PROD[Deploy to Production]
    APPROVE -->|Rejected| ROLLBACK[Rollback]
    
    PROD --> VERIFY[Verify Deployment]
    VERIFY --> MONITOR[Monitor Health]
    
    ROLLBACK --> NOTIFY[Notify Team]
    MONITOR --> SUCCESS[Deployment Complete]
    
    style DEV fill:#e8f5e8
    style TEST fill:#e1f5fe
    style PROD fill:#fff3e0
    style SUCCESS fill:#e8f5e8
    style ROLLBACK fill:#ffebee
```

---

**These diagrams provide a comprehensive visual understanding of the Aremu system's architecture, data flow, and operational processes.**
