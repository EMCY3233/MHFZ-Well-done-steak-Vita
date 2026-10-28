# INI load-holder copy and allocator contract

Static evidence uses unchanged ELF SHA256 2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d and the existing Ghidra 12.1.4/VitaLoaderRedux laboratory database. Function 0x82122426 was inspected in original instruction form, not executed. Its decompiler's missing allocator argument is resolved below from register flow.

On the inspected completed-read branch:

| Quantity | Holder field | Original observation |
|---|---|---|
| Source address S | +0x124 | Loaded at 0x82122606; a zero value bypasses preparation |
| Allocation/clearing capacity C | +0x128 | Loaded into r0 at 0x821225fe; zero bypasses preparation |
| Copied byte count N | +0x12c | Loaded at 0x8212260e and used as memcpy length |
| Receiver's owned input P | receiver +0x04 | New allocation stored at 0x82122620 |
| Receiver's recorded size | receiver +0x1c | C is stored at 0x82122612 |

At 0x82122616 the imported array-allocation entry receives r0=C, which is still the holder capacity. The resulting allocation is cleared for exactly C bytes at 0x82122624. At 0x82122630 memcpy receives destination P, source S and length N. A subsequent nonzero-pointer/nonzero-size branch leads to the parser call at 0x82122786. This distinguishes allocation size from copied byte count without relying on the inferred operator-new signature.

The parser's previously verified cleanup frees P and clears receiver field +0x04. After the parser returns, the load-holder cleanup conditionally frees S through the array-deallocation import at 0x821227e6, then clears holder fields +0x124/+0x128. Thus source-holder ownership and parser-input ownership are separate. A bridge must not alias these two allocations or use the persistent snapshot pool for either ownership transfer.

No comparison proving N<=C was identified in this local preparation segment. This does not prove the producer omits that invariant: it may establish it before publishing holder state. Likewise clearing C bytes supplies zero padding only where bytes remain after the N-byte copy; it is not a guaranteed terminator if N==C and no zero exists in the copied bytes. Parser state/encoding still require separate validation. These are input-contract obligations, not a demonstrated reachable memory error.

Requirements before a bridge can be connected:

1. Trace the producer of holder fields +0x124/+0x128/+0x12c and its completion state, including partial reads and failure cleanup.
2. Preserve distinct source and parser allocations with the proven compatible array allocator/deallocator; no malloc/new-array equivalence is assumed.
3. Validate N, C, source extent, termination and overflow before allocation/copy. Do not reproduce unchecked behavior simply for compatibility.
4. Keep copied content, allocation capacity, original 512000-byte save entry and private-record payload length as distinct values. Shortened records still lack round-trip evidence.
5. Account for both live allocations and temporary parser/serializer strings. Fixed-pool totals do not represent peak process memory.

This resolves the immediate allocator argument and copy order, but does not implement a bridge or prove runtime receiver identity, complete format, all error branches or Vita memory availability. The existing native payload limit stays 163840. No client, commercial function, console, firmware, plugins or original installation changed. Private instruction evidence remains ini-load-instructions-private.txt; no code bytes or pseudocode are published.