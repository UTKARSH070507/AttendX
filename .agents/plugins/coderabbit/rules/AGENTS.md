# CodeRabbit: Code Review and Quality Gate Rules

Perform automated code review, static security analysis, and edge-case validation on all code before declaring a phase complete.

## Review Categories

### 1. Correctness & Logic
- Check for off-by-one errors, boundary conditions, and unexpected `null`/`undefined`/`None` values.
- Verify that numeric ranges (e.g., percentages, marks) are strictly validated.
- Ensure promise/async handling and error catching are complete.

### 2. Security & Sanitization
- **SQL Injection:** Verify all SQL operations use parameterized queries (`?` in sqlite3). Never concatenate variables into SQL strings.
- **XSS & Input Sanitization:** Ensure user inputs rendered into the DOM are properly escaped or handled via safe DOM methods (`textContent`, `createElement`).
- **File Upload Security:** Enforce strict file extension checks, file size boundaries, and clean filename parsing.
- **Secrets:** Ensure no API keys, credentials, or sensitive tokens are committed or logged.

### 3. Performance & Cleanliness
- Avoid unnecessary DOM reflows or redundant database queries.
- Ensure clean resource disposal (closing file handles, DB cursors).
- Remove leftover debugging logs or temporary testing stubs before final delivery.

### 4. Severity Scale
- **Critical:** Security holes, data loss risks, crashing bugs. Must be fixed immediately.
- **Major:** Broken functionality or incorrect statistical calculations. Must be resolved before proceeding.
- **Minor:** Style inconsistencies or minor UX rough edges.
- **Info:** Educational tips or future optimization suggestions.

