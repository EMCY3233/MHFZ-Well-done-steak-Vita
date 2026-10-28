# Native complete-snapshot recovery

The freestanding ARM/Thumb selector validates both private manifests and every referenced record before selecting a generation. An incomplete newer generation falls back to the complete older generation as a whole. It never combines individually newest files. Conflicting manifests with equal generations fail closed; identical ties select slot zero.

The ARM harness passes 23 synthetic cases, including interrupted second-member preparation, orphan records, missing slots, sequence mismatches, record corruption, manifest truncation, conflicting generations, and digest callback failure. Error and absence paths preserve the caller output. The result file records the test artifact hash.

SHA-256 is supplied by a Python hashlib callback in this harness. This does not establish a native digest implementation, Vita file access, durable publication, locking, client integration, or physical isolation. Returned payload views borrow immutable caller memory. Both absent manifests do not authorize initialization or writes.

The next prerequisite is coherent batch preparation and publication with pinned references and a verified native digest. The existing two-slot layout does not guarantee two historical complete snapshots: preparing a candidate may invalidate references older than the currently selected snapshot. Falling back may lose the interrupted update.

Only original source and synthetic test metadata are included. No commercial executable or game resources are published. No client or console execution was performed.