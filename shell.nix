{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python39.withPackages (ps: with ps; [
      tkinter
    ]))
    python39Packages.poetry
    stdenv.cc.cc.lib
  ];
  shellHook = ''
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.stdenv.cc.cc.lib}/lib
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.libGL}/lib
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.zlib}/lib
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.glibc}/lib
  '';
}
