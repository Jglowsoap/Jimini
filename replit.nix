{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.nodejs_20
    pkgs.nodePackages.npm
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
  ];
  
  env = {
    PYTHONPATH = "$REPL_HOME";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
    ];
  };
}
