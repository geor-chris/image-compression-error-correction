# Image Compression & Error-Correction Pipeline

A client-server pipeline that implements lossless image compression using **Arithmetic Coding** and channel coding with a **Systematic Linear Error-Correcting Code (Hamming 7,4)**. Communication is handled over a **Flask RESTful API** with Base64 payload transport, JSON serialization, Shannon entropy calculations, and image verification.

---

## Architecture & Engineering Evolution

The project includes two implementations:

### 1. Chunked & Scalable Pipeline (`chunked_optimized/`) — Main Production
* **Arithmetic Coding with Chunking:** Processes data in fixed chunks (CHUNK_SIZE = 20 bytes), mapping each to a fixed-width binary representation (CHUNK_BITS = 800 bits). This resolves precision underflow issues on large image streams without losing boundary context.
* **Systematic Hamming (7, 4) Code:** Utilizes a generator matrix G = [I_4 | P] and parity matrix H = [P^T | I_3] with an established syndrome decoding table, guaranteeing 100% correction for 1-bit errors per 7-bit block.
* **Direct Bitstream Decompression:** Directly passes corrected bitstreams into arithmetic decoding without redundant decimal conversions.

### 2. Baseline Direct Pipeline (`baseline_direct/`) — Academic Reference
* **Pure Arithmetic Compression:** Encodes the entire input byte stream into a single fraction in [0, 1) using high-precision decimals (`Decimal(prec=5000)`).
* **Dynamic Linear Block Code:** Generates dynamic parity matrices P and tests generic syndrome decoding against small bitmaps (`tiny.gif`).

---

## Transmission Pipeline Overview

1. **Client Processing:**
   * Reads raw image bytes and calculates reference **SHA-256** hash.
   * Computes symbol occurrence probabilities and compresses the stream via Arithmetic Coding.
   * Encodes the bitstream into (7, 4) linear blocks with appropriate padding.
   * Injects simulated random channel bit flips (X% user-defined error rate).
   * Serializes the corrupted bitstream as Base64 inside a JSON payload and transmits via `POST /upload`.

2. **Server Processing:**
   * Decodes the Base64 bitstream and reconstructs the parity check matrix H.
   * Computes syndromes (S = r * H^T mod 2), identifies error patterns, and repairs corrupted blocks.
   * Reverses Arithmetic Coding back to raw bytes.
   * Validates image header integrity via **Pillow (`PIL.Image.verify`)**.
   * Computes Shannon entropy (H = -sum(p * log2(p))) and verifies data integrity against client SHA-256.

