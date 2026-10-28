# Native SHA-256 for private records

sha256.c/h implement the SHA-256 computation from the primary NIST specification, FIPS 180-4 sections 4.1.2, 4.2.2, 5 and 6.2: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf . This is original source, without copying a third-party implementation. This experiment is not NIST/FIPS certified.

The one-shot callback accepts at most 512036 bytes, the current structural record bound; it does not increase the native writer payload limit. It requires valid immutable input and a disjoint 32-byte output. NULL input is accepted for length zero. NULL output, nonempty NULL input, and excess length return -1 before output changes. No allocation, OS services or external undefined symbols are needed.

check_sha256_arm.py executes the compiled computation under ARM/Thumb and compares its output with Python hashlib as an independent oracle. There is no digest hook. Nineteen cases pass: empty/abc, unaligned buffers, 55/56/63/64/65 and 119/120/127/128/129 byte boundaries, record limits 163876/512036, and invalid arguments. sha256-arm-results.json records digests and the generated original test ELF hash. The test ELF is not published.

check_snapshot_native_sha_arm.py links this implementation with the original manifest, record-reference and complete-snapshot readers. Its 23 snapshot cases pass without Python digest substitution. Its forced error case uses a native failure stub. Corrupt and conflicting snapshots remain rejected, and incomplete newer snapshots fall back as a whole. snapshot-native-sha-arm-results.json records this separate coverage.

This verifies computation in emulation, not Vita execution, persistent storage, power-loss behavior or client integration. Native batch publication, ownership/locking, larger INI-DATA capacity, private mounts, AppUtil identity and executable isolation remain unresolved. No console or commercial client was executed.