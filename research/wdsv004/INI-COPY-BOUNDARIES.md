# INI serializer copy-boundary verification

Static target: aligned entry 0x82123582, same ELF SHA256 2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d. Original instruction listings were read through the existing laboratory Ghidra database. The target function was not executed or emulated.

The entry saves incoming r2 and r1 into stack offsets 0x24 and 0x28 at 0x821235a2. The tail loads the capacity from offset 0x24 at 0x821237b0 and compares it with the constructed string length at 0x821237b2. The unsigned carry-set branch at 0x821237b6 skips truncation when capacity is at least length. Otherwise, 0x821237b8 substitutes capacity minus one. The resulting copy count is passed to memcpy at 0x821237c8. The zero terminator is stored at destination plus that count at 0x821237d0. Finally, 0x821237dc sets return register r0 to 1. This confirms a constant result in the observed ordinary epilogue, not an output-length return.

| Capacity C / text length L | Derived count | Terminator index | Within an exactly C-byte destination? |
|---|---:|---:|---|
| C greater than L | L | L | Yes |
| Positive C less than L | C minus 1 | C minus 1 | Yes for the final copy/terminator only |
| Positive C equal to L | L | C | The terminator is one past capacity |
| C zero, L zero | 0 | 0 | No destination byte is available |
| C zero, L positive | 0xffffffff after unsigned subtraction | 0xffffffff | Not a valid bounded-copy operation |

This table is arithmetic derived from the branch and register flow, not runtime testing. It excludes temporary-string construction, allocator failures, source validity and other memory effects. In the known save-worker path C is positive 512000; no evidence establishes that the exact-equality text length is reachable there. Accordingly this is a boundary-contract limitation, not a demonstrated game crash or exploit. Do not patch the original or reproduce this behavior blindly in new code.

The worker keeps the original 512000-byte save entry size in the bounded evidence. Constant return value 1 cannot be treated as serialized length. Shrinking private records to a text prefix or changing zero padding requires reader compatibility evidence. No capacity changes were made. The pending counterpart is virtual slot 0x18, whose table word points to Thumb 0x8212301f, aligned entry 0x8212301e; its role must be inspected rather than inferred solely from adjacency.

Private instruction listings remain ini-copy-head-private.txt and ini-copy-tail-private.txt. This public report contains only addresses, effects and derived boundary metadata. No code bytes or pseudocode are published. No client, console, firmware/plugins or original installation changed.