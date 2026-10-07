# M1 review corrections

Scope: the three reported defects only; the physical model and full roadmap remain
unchanged. Historical M1 evidence is retained but does not verify these corrections.
New results identify source/configuration hashes and the actual environment.

## Acceptance

1. M1-REQ-007: lose control and protection STEP replies independently after plant
   acceptance. Attempt both services but send no COMMIT/ADVANCE for the failed
   tick. HALT cancels pending decisions permanently; late commands cannot resume
   the run. Record cause, acknowledgment and independently observed state. Failed
   HALT/STATUS leaves the appropriate state unconfirmed. Test real processes and
   call order, including the plant's eventual autonomous watchdog.
2. M1-REQ-008: stream the existing supported 100000 ticks without full trajectory
   storage/serialization copies. Acceptance fixed before memory measurement: peak
   runner RSS <=64 MiB under the unchanged 128 MiB Compose limit, leaving >=64 MiB
   RSS headroom. Measure RSS and actual container execution, count/order, repeated
   byte hashes and complete-prefix recovery after interruption. Container accounting
   includes reclaimable page cache; RSS headroom is not unused cgroup memory.
3. M1-REQ-009: collect logs and available artifacts after nonzero Compose exit;
   preserve the original code and record collection failures separately. Failed
   extraction retains result volumes and stopped containers with recovery commands.
   Exercise aborted runner, pre-start failure and extraction failure, including
   real Docker artifact recovery before test-owned cleanup.

## Implementation and verification sequence

- Correct abort arbitration and add real-socket lost-reply/failed-stop regressions.
- Version streaming JSONL output, update readers, and test RSS and interruption.
- Collect Compose evidence before cleanup; test command order and real failures.
- Run existing native, sanitizer, assurance and Docker checks; retain new evidence,
  update trace links and status, and keep incomplete release gates blocked.

No model equation, supported tick count, dependency pin, memory allowance or release
check is relaxed. Independent review, clinical validation and all roadmap release
obligations remain open. See the final evidence/status record for actual execution.
