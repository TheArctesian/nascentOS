{
  description = "Scoped nascentOS VPN evaluation; no clients built or networks changed";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/cd4ea8d57de16f4810bc5f14207bac45fbf19f67";
  outputs = { nixpkgs, ... }: {
    nixosModules.default = import ./module.nix;
    # Evaluation-only evidence, usable from Darwin without fetching Linux clients.
    validation = import ./tests/eval.nix { inherit nixpkgs; };
    formatter = nixpkgs.lib.genAttrs [
      "aarch64-darwin"
      "x86_64-darwin"
      "aarch64-linux"
      "x86_64-linux"
    ] (system: nixpkgs.legacyPackages.${system}.nixfmt);
  };
}
