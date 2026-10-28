# INI-DATA memory and lifetime assessment

The static worker evidence in WDSV003 LARGE-INI-ENTRY.md records an allocation and entry size of 512000 bytes, plus an optional virtual serializer on container field zero. Its target, actual format and read validation remain unresolved. This is evidence of the worker's capacity, not proof that every save has 512000 meaningful bytes or that an all-zero synthetic value is compatible.

check_memory_budget.py compiles only original WDSV004 C sources with the existing ARM GCC, -Os and -fstack-usage. It checks ARM structure sizes at compile time: private pool 983636 bytes, plan 208, snapshot 44, callbacks 16. No executable or commercial client is run. memory-budget-results.json records compiler, flags, source hashes, individual frame metadata and calculations.

| Policy | Read pool bytes | Three independent replacement buffers | Subtotal |
|---|---:|---:|---:|
| Existing 163840-byte payload limit for each logical member | 983636 | 491628 | 1475264 |
| Hypothetical INI-only 512000-byte payload | 1679956 | 839788 | 2519744 |
| Hypothetical 512000-byte payload for all three members | 3072596 | 1536108 | 4608704 |

Each encoded record adds 36 bytes. The pool holds two record slots per member, two 188-byte manifests and the four-byte prerequisite flag. Replacement buffers are separate because the adapter rejects pool aliases and reuses observation memory on every read. The INI-only scenario adds 1044480 bytes relative to the existing subtotal; increasing all members costs substantially more and has no current evidence-based justification. Neither hypothetical policy is implemented or authorized as a physical integration result.

Compiler frame metadata includes commit 832 bytes, prepare 712, recover 488, record resolution 72, SHA entry 184 and compression block 336. Summing these along the expected nested validation path gives 2624 bytes of reported frames. This is accounting, not a whole-program stack guarantee: optimization, ABI call alignment, indirect callbacks, OS/library calls, exceptions/interrupts and reentrancy require separate analysis. No client thread stack or memory availability has been measured. Never place the roughly megabyte-sized pool on the thread stack.

The subtotal excludes the game's existing 512000-byte allocation, other game buffers, renderer/resources, allocator overhead, independent copies retained by callers and OS memory. A lower-memory streaming redesign would require a new ownership and validation protocol; it cannot simply release old buffers while borrowed snapshots still reference them. The final snapshot borrows the latest observation and expires when the pool is reused. Replacement sources must remain immutable throughout commit. The actual game's asynchronous worker ownership has not yet been integrated with these rules.

Decision: keep the current capacity unchanged. A future INI-only design should first prove serializer length/format and buffer ownership, then implement a separately reviewed per-logical capacity policy and boundary/interruption tests. This report supplies a quantified design constraint, not a memory-safety or launch approval. Native storage composition is tested in emulation; real mounts, identity, exclusivity and persistence remain unproven. No console changes occurred.