# INI parser ownership and terminator evidence

Static target 0x82121882 is a 2974-byte recorded function in the unchanged ELF SHA256 2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d. Ghidra 12.1.4/VitaLoaderRedux decompiles it with unreachable-block and unresolved-type-propagation warnings. Those warnings are retained in private evidence; recovered types are not an established ABI. The function was not executed or emulated.

The original entry loads a source pointer from receiver offset 0x04 at 0x821218a8. In the scanning path a byte is loaded at 0x821218dc. The original branch at 0x82121da2/0x82121da6 tests the current byte for zero and transfers to the next processing phase; newline handling follows on the nonzero branch. The surrounding flow distinguishes selected multibyte lead ranges and maintains parser state, so this is not proof of a universal strlen-only grammar or safe truncation at arbitrary bytes.

The decompilation shows section/key/value-like processing, selected comment/separator tests, temporary strings and insertion into the receiver's grouped collections through 0x82120f24. It calls strlen on intermediate strings. Full encoding, malformed input behavior, duplicate-key rules, allocation failure and whether every relevant branch is bounded by the original byte count remain unproven. In particular the observed scan is pointer/terminator driven; no whole-parser bounded-buffer guarantee is inferred.

The ownership finding is stronger: at 0x82122384 the cleanup path loads receiver field 0x04, tests it, calls the imported array-deallocation entry at 0x8212238a and clears field 0x04 at 0x8212238e. This matches the preceding load path that allocates and copies into receiver-owned storage. It is not merely a borrowed pointer that can safely reference the private adapter's persistent pool.

Consequences for integration:

- Never assign a snapshot's borrowed pool view directly to receiver field 0x04. The parser may deallocate that address; the pool is persistent caller-owned storage and must survive future observations.
- Any bridge must establish a separate allocation with the exact compatible allocator/deallocator contract, copy a validated terminated value into it and transfer ownership explicitly. No new[]/delete[] versus malloc/free equivalence is assumed.
- The final snapshot view expires at the adapter's next read. Copying, parsing and worker completion must therefore have a documented order and an independently owned source throughout any asynchronous interval.
- Terminator-driven scanning does not authorize shortened private records or changing the worker's 512000-byte entry. Padding, copied length and allocation capacity remain distinct. A parser-compatible round trip is still missing.

This adds a receiver-owned input allocation and parser temporary allocations to the memory/lifetime analysis; the fixed pool/staging subtotal is not peak process memory. Native capacity stays at 163840 payload bytes. No allocator bridge, client hook, physical run or original installation change was made.

Private evidence: ini-parser-private.json and ini-parser-instructions-private.txt. Public evidence contains only source identity, function/branch addresses and observed ownership effects, without code bytes or pseudocode. Next focused work is the load-holder size/copy contract and exact allocator call arguments, followed by a reviewable bridge design; do not repeat the virtual-slot survey.