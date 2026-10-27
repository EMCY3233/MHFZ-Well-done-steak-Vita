"""Classify only the padding emitted by the pinned vita-make-fself policy."""
import zlib


def inspect_segment(raw, expected_size):
    if expected_size < 0:
        raise ValueError('negative decoded size')
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(raw, expected_size + 1)
    if not decoder.eof or decoder.unconsumed_tail or len(decoded) != expected_size:
        raise ValueError('invalid/truncated stream or decoded size')
    tail = decoder.unused_data
    stream_size = len(raw) - len(tail)
    expected_padding = (-stream_size) % 4
    canonical = len(tail) == expected_padding and tail == b'\0' * expected_padding
    return dict(decoded_bytes=len(decoded), stream_bytes=stream_size,
                trailing_bytes=len(tail), expected_padding_bytes=expected_padding,
                matches_pinned_padding_policy=canonical)