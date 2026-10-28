# Native owned-text handoff experiment

This own interface follows the investigation published at WDSV004 commit
4f1c255: [parser ownership](https://github.com/EMCY3233/MHFZ-Well-done-steak-Vita/blob/4f1c255/research/wdsv004/INI-PARSER-OWNERSHIP.md),
[load-holder contract](https://github.com/EMCY3233/MHFZ-Well-done-steak-Vita/blob/4f1c255/research/wdsv004/INI-LOAD-HOLDER-CONTRACT.md) and
[completion publication](https://github.com/EMCY3233/MHFZ-Well-done-steak-Vita/blob/4f1c255/research/wdsv004/INI-COMPLETION-PUBLICATION.md). A separate local Python reference has source
SHA256 3c213c4067f7e8e3b6b9874d6a801ee728772c64b92978519142fb4726873d2c;
it was consulted, not executed as commercial code or copied into the client.
The native interface is not a declaration of the client's ABI or class layout.

## Contract

A zero-initialized owner starts EMPTY. `wdsv004_text_prepare` requires a
caller-validated completed byte count equal to the expected count, bounded by
capacity (at most 512000), a sufficient source extent and a valid paired allocator.
A raw FIOS result is never interpreted as a byte count. The complete source is
borrowed and must remain immutable throughout preparation, including callbacks.
Only the explicitly selected prefix is copied. An interior NUL in that prefix
is rejected; unrelated trailing bytes are not interpreted or trimmed.

All length, source-range, source/owner overlap and terminator checks precede
allocation. The allocator receives N+1, including for empty input. It must return
fresh independent storage of exactly that extent, or a null/zero block on
allocation failure. After copying N bytes, the interface writes its own final NUL.
This does not establish that the game accepts this text, its encoding or empty input.

The owner is BUSY during allocation. On success it becomes OWNED and retains the
matching release function and context. A missing allocation returns NO_MEMORY
with no ownership transfer and leaves EMPTY for a deliberate retry. A malformed
allocator result makes the handle terminal FAILED. An independent nonnull result
with incorrect extent is returned once to its matching release callback.
A detected source/owner alias or wrapping result address is not freed, because
it cannot safely be treated as a fresh owned allocation. This is a broken-allocator
diagnostic, not guaranteed cleanup of arbitrary invalid allocator results.

`wdsv004_text_move` transfers ownership only into an EMPTY, nonoverlapping handle;
the destination must also be disjoint from the source owner's text block;
the original becomes terminal MOVED and loses its pointer and callbacks.
`wdsv004_text_dispose` clears an OWNED handle to terminal RELEASED **before**
invoking its callback. Disposing again or disposing a moved handle is rejected.
Callbacks therefore cannot cause a second disposal of that handle by reentry.

## Preconditions and limits

The caller must provide real readable/writable objects with valid lifetimes;
integer range checks are not memory mapping validation. Allocations must be
fresh, independent of every live object, and from the promised paired allocator.
The implementation detects selected aliases, not all invalid pointers or aliases
with arbitrary external objects. Owner handles must not be copied or edited and must remain outside all live
text allocations. The move operation rejects overlap with its source text block.
Callbacks must return normally, preserve source immutability and respect their
context lifetime. Use is exclusive and single-threaded: no lock, atomic
publication, cross-thread visibility or crash recovery is implemented.

Source ownership remains with the caller. Moving transfers an **own interface's**
handle, not ownership into the commercial parser. No new[]/delete[] versus
malloc/free equivalence is assumed. Binding the actual client allocator, object
layout, status mapping, async lifetime and parser format remains separate work.
The 512000 bound here does not expand the native record payload limit of 163840.

## Verification

`check_text_handoff_arm.py` compiles text_handoff.c plus a native synthetic
allocator/release fixture, with warnings as errors, freestanding ARM Thumb code
and no standard library. It checks that no undefined symbols remain. The whole
handoff and callbacks run under Unicorn; there are no Python allocation/free hooks
or executed commercial functions. The synthetic release callback counts and
checks ownership transitions but does not free a real heap allocation.
Python supplies synthetic inputs and checks
outputs, ownership states, callback counts and restored stack.

40 named scenarios cover exact capacity, zero and maximum lengths, independent
copy lifetime, explicit text prefix, incomplete/overreported counts, source
extent/range/owner overlap, missing callbacks, terminal states, allocation failure
and retry, incorrect extents, null with extent, borrowed/partial/owner aliases,
wrapping output, callback reentry, moves into self/overlapping/occupied handles,
and exactly-once cleanup after successful move. Overlapping expectations in this
suite are not separate proof of general memory safety.

The existing source-only ARM runner includes this tenth harness and requires
exactly 40 scenarios. The generated JSON records source/ELF hashes and scope;
CI uploads JSON only, not test executables. Existing snapshots and JSON evidence
are left intact when running through the temporary-tree runner. The direct
harness creates only its own test ELF and report.

Acceptance here is synthetic native ownership/copy behavior with the declared
preconditions. No parser-compatible round trip, client hooks, real allocator
binding, mount/isolation check, storage capacity change, Vita execution or
power-loss durability is claimed. Reversal is removal of this own implementation,
test and runner entry from its independent branch; no console state changes.

Next task: establish the real allocator/deallocator and result-status ABI plus
format/terminator policy before any adapter connects this interface to a client.
Do not use passing synthetic tests to authorize integration or installation.
