{
  description = "Scoped nascentOS interactive shell support";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/cd4ea8d57de16f4810bc5f14207bac45fbf19f67";
  outputs = { nixpkgs, ... }: {
    nixosModules.default = import ./module.nix;
    validation = import ./tests/eval.nix { inherit nixpkgs; };
    formatter.aarch64-darwin = nixpkgs.legacyPackages.aarch64-darwin.nixfmt;
  };
}
