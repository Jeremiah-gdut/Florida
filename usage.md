# Florida Usage

## Trigger Build

```bash
# Latest version
gh workflow run Florida -R Jeremiah-gdut/Florida

# Specific version
gh workflow run Florida -R Jeremiah-gdut/Florida -f frida_version=17.9.10

# Batch (16.0.0 - latest)
for v in $(gh api repos/frida/frida/tags --paginate --jq '.[].name' | grep -E '^\d+\.\d+\.\d+$' | sort -V | awk '$0 >= "16.0.0"'); do
  gh workflow run Florida -R Jeremiah-gdut/Florida -f frida_version=$v
done
```

## Check Status

```bash
# List recent runs
gh run list -R Jeremiah-gdut/Florida -w Florida -L 20

# Check releases with assets
gh release list -R Jeremiah-gdut/Florida -L 100

# Find empty releases
gh api repos/Jeremiah-gdut/Florida/releases --paginate --jq '.[] | select((.assets | length) == 0) | .tag_name'

# Delete empty release
gh release delete <tag> -R Jeremiah-gdut/Florida --yes
```

## Download

```bash
gh release download <tag> -R Jeremiah-gdut/Florida -D ./output
```
