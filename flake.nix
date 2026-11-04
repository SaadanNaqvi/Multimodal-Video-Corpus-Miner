{
  description = "Development environment for Multimodal Video Corpus Miner";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # Allowed for unfree packages like CUDA if you need GPU acceleration later
          config.allowUnfree = true; 
        };
      in
      {
        devShells.default = pkgs.mkShell {
          # 1. System-level packages your video miner will need
          buildInputs = with pkgs; [
            python311                  # Fixed Python version. pip comes from the venv:
                                       # python311Packages.* here would leak in through PYTHONPATH
            git                        # macOS's /usr/bin/git can't run with this shell's DEVELOPER_DIR

            # Heavy lifting media/data dependencies
            ffmpeg-full                # Full FFmpeg suite for video manipulation
            pkg-config                 # Helps Python wheels find system C-libraries
            stdenv.cc.cc.lib           # Standard C++ library (crucial for scipy/numpy/opencv wheels)
            zlib
            glib
          ];

          # 2. Environment variables to tell Python where to find C-libraries
          shellHook = ''
            # Rebuild the venv if it doesn't use the flake's Python
            PY=${pkgs.python311}/bin/python
            if [ "$(readlink .venv/bin/python)" != "$PY" ]; then
              echo "Creating virtual environment..."
              "$PY" -m venv --clear .venv
              .venv/bin/python -m pip install --upgrade pip
            fi

            # Activate the virtual environment automatically
            source .venv/bin/activate

            # Nix's Python sets this, and it would take priority over the venv's packages
            unset PYTHONPATH

            ${pkgs.lib.optionalString pkgs.stdenv.isDarwin ''
              # Nix's git doesn't read Apple's git config, which is where the keychain login is set
              export GIT_CONFIG_COUNT=1
              export GIT_CONFIG_KEY_0=credential.helper
              export GIT_CONFIG_VALUE_0=osxkeychain
            ''}

            # Fixes common binary wheel loading errors (like OpenCV, PyTorch, etc.) looking for glibc
            export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
            export PKG_CONFIG_PATH=${pkgs.ffmpeg-full.dev}/lib/pkgconfig:$PKG_CONFIG_PATH

            echo "🎥 Multimodal Video Corpus Miner environment active!"
            echo "Python: $(python --version)"
            echo "FFmpeg: $(ffmpeg -version | head -n 1)"
          '';
        };
      });
}
