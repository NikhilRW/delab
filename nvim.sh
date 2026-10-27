
#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/NikhilRW/my-lazyvim-config.git"
CONFIG_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}"
CONFIG="$CONFIG_ROOT/${NVIM_APPNAME:-nvim}"
INSTALL_ROOT="$HOME/.local/opt"
BIN_DIR="$HOME/.local/bin"

echo "==> Installing LazyVim on GitHub Codespaces"

# 1. Install Linux dependencies
if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script requires Ubuntu/Debian." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y \
  git curl ca-certificates tar gzip unzip \
  build-essential ripgrep fd-find fzf \
  nodejs npm python3 python3-pip

mkdir -p "$BIN_DIR" "$INSTALL_ROOT" "$CONFIG_ROOT"

# Ubuntu names the fd executable fdfind
if ! command -v fd >/dev/null 2>&1; then
  ln -sf "$(command -v fdfind)" "$BIN_DIR/fd"
fi

# 2. Install current stable Neovim
case "$(uname -m)" in
  x86_64|aarch64)
    ARCH="$(uname -m)"
    ;;
  *)
    echo "Unsupported CPU architecture" >&2
    exit 1
    ;;
esac

NVIM_DIR="$INSTALL_ROOT/nvim-linux-$ARCH"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Downloading Neovim ($ARCH)"

curl -fL --retry 3 \
  "https://github.com/neovim/neovim/releases/latest/download/nvim-linux-$ARCH.tar.gz" \
  -o "$TMP_DIR/nvim.tar.gz"

tar -xzf "$TMP_DIR/nvim.tar.gz" -C "$TMP_DIR"

rm -rf "$NVIM_DIR"
mv "$TMP_DIR/nvim-linux-$ARCH" "$NVIM_DIR"
ln -sf "$NVIM_DIR/bin/nvim" "$BIN_DIR/nvim"

# Make tools available in this shell and future SSH shells
export PATH="$BIN_DIR:$PATH"

for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
  if [ -f "$RC" ] && ! grep -Fq \
    'export PATH="$HOME/.local/bin:$PATH"' "$RC"; then
    printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$RC"
  fi
done

# 3. Check minimum Neovim version
nvim --headless -u NONE -i NONE \
  '+lua if vim.fn.has("nvim-0.11.2") == 0 then error("Neovim >= 0.11.2 required") end' \
  +qa

# 4. Install Tree-sitter CLI
echo "==> Installing Tree-sitter CLI"

npm install --global --prefix "$HOME/.local" \
  tree-sitter-cli

# 5. Install lazygit
echo "==> Installing lazygit"

if ! command -v lazygit >/dev/null 2>&1; then
  LAZYGIT_VERSION="$(curl -fsSL \
    https://api.github.com/repos/jesseduffield/lazygit/releases/latest \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))')"

  case "$ARCH" in
    x86_64) LG_ARCH="x86_64" ;;
    aarch64) LG_ARCH="arm64" ;;
  esac

  curl -fL --retry 3 \
    "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_Linux_${LG_ARCH}.tar.gz" \
    -o "$TMP_DIR/lazygit.tar.gz"

  tar -xzf "$TMP_DIR/lazygit.tar.gz" \
    -C "$TMP_DIR" lazygit

  install -m 755 "$TMP_DIR/lazygit" "$BIN_DIR/lazygit"
fi

# 6. Install your Neovim configuration
echo "==> Installing your LazyVim config"

ORIGIN=""
if [ -d "$CONFIG/.git" ]; then
  ORIGIN="$(git -C "$CONFIG" remote get-url origin 2>/dev/null || true)"
fi

case "$ORIGIN" in
  "$REPO"|https://github.com/NikhilRW/my-lazyvim-config|git@github.com:NikhilRW/my-lazyvim-config.git)
    echo "Existing preset found; preserving local edits."
    ;;
  *)
    if [ -e "$CONFIG" ] || [ -L "$CONFIG" ]; then
      BACKUP="$(mktemp -d "$CONFIG_ROOT/nvim-backup.XXXXXX")"
      mv "$CONFIG" "$BACKUP/config"
      echo "Previous config backed up to $BACKUP/config"
    fi

    git clone --depth 1 --branch main "$REPO" "$CONFIG"
    ;;
esac

if [ ! -f "$CONFIG/init.lua" ]; then
  echo "Error: init.lua missing in $CONFIG" >&2
  exit 1
fi

# 7. Restore LazyVim plugins
echo "==> Restoring plugins"

nvim --headless '+Lazy! restore' +qa

echo ""
echo "=================================="
echo " LazyVim installation complete!"
echo "=================================="
echo "Neovim: $(nvim --version | head -n 1)"
echo "Config: $CONFIG"
echo ""
echo "Run: nvim"
echo "Health check: :checkhealth"
