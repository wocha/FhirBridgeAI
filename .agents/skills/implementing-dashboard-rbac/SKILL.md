---
name: implementing-dashboard-rbac
description: Standard for implementing basic, local Role-Based Access Control (RBAC) in Streamlit dashboards for KRITIS environments.
---

# Implementing Dashboard RBAC

In a KRITIS environment, dashboards exposing system internals (like audit logs, error traces, or queue states) must not be accessible to unauthorized personnel.
While enterprise deployments often use Keycloak and OIDC (via oauth2-proxy), local testing and simpler deployments can achieve high security using `streamlit-authenticator`.

## Core Requirements

1. **Authentication First:** The dashboard must be completely inaccessible until a valid login occurs.
2. **Role-Based Access Control (RBAC):** Users must be assigned roles.
    * `viewer`: Can see high-level aggregate metrics.
    * `auditor`: Can see detailed error traces, payloads, and audit logs.
3. **Stateless Sessions:** Use secure JWTs for maintaining sessions.
4. **Secure Defaults:** Passwords must be hashed (e.g., using bcrypt).

## Implementation Strategy

1. Add `streamlit-authenticator` and `bcrypt` to dependencies.
2. Initialize an `Authenticator` instance in the main Streamlit file (`app.py`).
3. Define standard roles in the authenticator config (`viewer`, `auditor`).
4. Wrap all dashboard rendering logic in an authentication check (`authenticator.login()`).
5. In the UI rendering functions, check `st.session_state["roles"]` (if provided, or map usernames to roles manually) and conditionally render sensitive components like `st.expander` containing stack traces.

### Example

```python
import streamlit as st
import streamlit_authenticator as stauth

config = {
    'credentials': {
        'usernames': {
            'viewer': {'email': 'viewer@example.com', 'name': 'Viewer', 'password': '...hashed...', 'role': 'viewer'},
            'auditor': {'email': 'auditor@example.com', 'name': 'Auditor', 'password': '...hashed...', 'role': 'auditor'}
        }
    },
    'cookie': {'expiry_days': 1, 'key': 'kritis_dashboard_signature', 'name': 'kritis_dashboard_session'},
    'pre-authorized': {'emails': []}
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state['authentication_status']:
    # Show dashboard
    role = config['credentials']['usernames'][st.session_state['username']]['role']
    if role == 'auditor':
        # Show sensitive traces
        pass
```
