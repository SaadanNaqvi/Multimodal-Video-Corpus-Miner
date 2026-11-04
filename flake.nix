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
            python311                  # Fixed Python version
            python311Packages.pip      # Pip inside the environment
            python311Packages.virtualenv
            
            # Heavy lifting media/data dependencies
            ffmpeg-full                # Full FFmpeg suite for video manipulation
            pkg-config                 # Helps Python wheels find system C-libraries
            stdenv.cc.cc.lib           # Standard C++ library (crucial for scipy/numpy/opencv wheels)
            zlib
            glib
          ];

          # 2. Environment variables to tell Python where to find C-libraries
          shellHook = ''
            # Create a virtual environment if it doesn't exist
            if [ ! -d ".venv" ]; then
              echo "Creating virtual environment..."
              python -m venv .venv
            fi

            # Activate the virtual environment automatically
            source .venv/bin/activate

            # Ensure pip is up to date inside the venv
            pip install --upgrade pip setuptools wheel

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
