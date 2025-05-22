┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ API Clients         │     │ Flask LLM API       │     │ Token Storage       │
│                     │     │                     │     │                     │
│ - Existing clients  │────▶│ - Token validation  │────▶│ - Encrypted storage │
│ - New clients       │     │ - Scope enforcement │     │ - Token metadata    │
└─────────────────────┘     │ - Admin endpoints   │◀────│ - Lifecycle tracking│
                            └─────────────────────┘     └─────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │ CLI Management Tool │
                            │                     │
                            │ - Token creation    │
                            │ - Token rotation    │
                            │ - Token revocation  │
                            └─────────────────────┘