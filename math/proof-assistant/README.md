# Proof Assistant

```sh
# Install Lean4 (Mac/Linux)
brew install elan-init

# > info: downloading https://releases.lean-lang.org/lean4/v4.23.0/lean-4.23.0-darwin_aarch64.tar.zst
# > Total: 403.0 MiB Speed:   8.8 MiB/s
# > info: installing /Users/saifulislam/.elan/toolchains/leanprover--lean4---v4.23.0
# > leanprover/lean4:v4.23
elan toolchain install leanpower/lean4:stable

# > info: default toolchain set to 'leanprover/lean4:stable'
elan default leanprover/lean4:stable

# verify the output
lean --version
# > Lean (version 4.23.0, arm64-apple-darwin23.6.0, commit 50aaf682e9b74ab92880292a25c68baa1cc81c87, Release)

# creating a new lake playground
lake new lean_playground
cd lean_playground
```
