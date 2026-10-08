#!/usr/bin/env python3
"""Encode the actual project-rendered RGB framebuffer; no external image assets."""
import argparse
import struct
from pathlib import Path
import zlib


def encode(width, height, rgb):
    if not 0 < width <= 4096 or not 0 < height <= 4096 or len(rgb) != width * height * 3:
        raise ValueError('RGB framebuffer dimensions')
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    scanlines = b''.join(b'\0' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scanlines, 9)) + chunk(b'IEND', b''))


def validate_owned_png(raw):
    """Only our bounded RGB8/filter-0 encoder profile; reject metadata/extra payloads."""
    if len(raw) > 20 * 1024 * 1024 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('owned image format')
    offset, chunks = 8, []
    while offset < len(raw):
        if len(raw) - offset < 12: raise ValueError('PNG chunk')
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + size]
        if offset + 12 + size > len(raw): raise ValueError('PNG length')
        crc = struct.unpack('>I', raw[offset + 8 + size:offset + 12 + size])[0]
        if crc != zlib.crc32(kind + data): raise ValueError('PNG CRC')
        chunks.append((kind, data)); offset += size + 12
    if [c[0] for c in chunks] != [b'IHDR', b'IDAT', b'IEND'] or chunks[-1][1]: raise ValueError('PNG profile')
    if len(chunks[0][1]) != 13: raise ValueError('PNG header')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    if not 0 < width <= 4096 or not 0 < height <= 4096 or (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError('PNG dimensions/profile')
    expected = height * (1 + width * 3)
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(chunks[1][1], expected + 1)
    if len(pixels) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PNG pixel length')
    if any(pixels[y * (width * 3 + 1)] for y in range(height)): raise ValueError('PNG filter')
    return width, height


def convert(source, target):
    with Path(source).open('rb') as stream:
        if stream.readline() != b'P6\n': raise ValueError('framebuffer format')
        width, height = map(int, stream.readline().split())
        if stream.readline() != b'255\n': raise ValueError('framebuffer depth')
        data = encode(width, height, stream.read())
    validate_owned_png(data)
    with Path(target).open('xb') as output: output.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('target', type=Path)
    args = parser.parse_args(); convert(args.source, args.target)
