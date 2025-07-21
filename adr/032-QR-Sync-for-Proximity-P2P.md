# 032. QR Sync for Proximity P2P

- **Status:** Accepted
- **Date:** 1/27/2025

## Context

In physical proximity settings (classrooms, conferences, study groups), users need a reliable way to share blockchain state without relying on internet connectivity or complex P2P discovery mechanisms. Traditional WebRTC connections may fail due to network restrictions, NAT traversal issues, or firewall configurations common in educational environments.

The current P2P implementation requires active network connections for peer discovery and data exchange, which can be unreliable in offline or restricted network scenarios where users are physically close but cannot establish direct connections.

## Decision

We will implement a QR code-based synchronization system inspired by Bitchat's offline messaging approach, but optimized for blockchain delta synchronization. This system will enable proximity-based chain state sharing through visual QR codes.

### Key Components:

1. **Block Serialization & Chunking**:
   - Serialize blocks into compact binary format (~3KB per block)
   - Split large payloads across 2-3 QR codes using chunking protocol
   - Each QR code contains: chunk index, total chunks, block hash, and chunk data

2. **QR Generation Flow**:
   - UI button "Generate QR" triggers block delta calculation
   - Use merkle tree diff to identify missing blocks between peers
   - Generate sequence of QR codes for efficient scanning
   - Display QR codes in rotation (3-second intervals)

3. **QR Scanning & Merge**:
   - "Scan QR" button activates webcam component
   - jsQR library processes camera frames for QR detection
   - Reconstruct blocks from multi-QR chunks
   - Merge received chain deltas using merkle diff validation
   - Update local blockchain state with verified blocks

4. **Reliability Features**:
   - QR-only approach (no network fallback) for maximum reliability
   - Checksum validation for each chunk
   - Automatic retry for failed chunk reconstruction
   - Visual feedback for successful/failed scans

### Technical Implementation:

- **Generation**: `qrcode` library for QR generation
- **Scanning**: `jsQR` library for webcam-based QR detection
- **Chunking**: Custom protocol with chunk metadata
- **Merkle Diff**: Leverage existing core chain comparison logic
- **UI**: Minimal buttons integrated into existing P2P interface

## Consequences

**Positive:**
- Enables offline blockchain synchronization in proximity settings
- Reliable in restricted network environments (schools, conferences)
- Visual feedback provides clear user experience
- Leverages existing merkle tree infrastructure for efficient deltas
- No external dependencies beyond QR libraries
- Works across different devices and platforms

**Negative:**
- Manual process requiring user interaction for each sync
- Limited to small block sets due to QR data capacity constraints
- Requires camera access permissions
- May be slower than direct network transfer for large datasets
- QR scanning requires good lighting conditions
- Multi-QR sequences need careful coordination to avoid user confusion

**Risks:**
- QR code scanning reliability depends on camera quality and lighting
- User must manually coordinate QR generation and scanning sequence
- Potential for incomplete transfers if QR sequence is interrupted 