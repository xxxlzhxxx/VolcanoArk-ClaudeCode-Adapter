#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${CLAUDE_CODE_VERSION:-2.1.216}"
PLATFORM="${CLAUDE_CODE_PLATFORM:-darwin-arm64}"
VENDOR_DIR="$ROOT_DIR/vendor"

mkdir -p "$VENDOR_DIR" "$VENDOR_DIR/native/$PLATFORM"

curl -sSfL "https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-$VERSION.tgz" \
  -o "$VENDOR_DIR/claude-code-$VERSION.tgz"
rm -rf "$VENDOR_DIR/package"
tar -xzf "$VENDOR_DIR/claude-code-$VERSION.tgz" -C "$VENDOR_DIR"

curl -sSfL "https://registry.npmjs.org/@anthropic-ai/claude-code-$PLATFORM/-/claude-code-$PLATFORM-$VERSION.tgz" \
  -o "$VENDOR_DIR/claude-code-$PLATFORM-$VERSION.tgz"
rm -rf "$VENDOR_DIR/native/$PLATFORM/package"
tar -xzf "$VENDOR_DIR/claude-code-$PLATFORM-$VERSION.tgz" -C "$VENDOR_DIR/native/$PLATFORM"
chmod +x "$VENDOR_DIR/native/$PLATFORM/package/claude"

echo "Installed Claude Code $VERSION for $PLATFORM under $VENDOR_DIR"
