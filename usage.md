# Florida Usage

## Download

```
https://github.com/Jeremiah-gdut/Florida/releases
```

Each release contains the following files per arch (`arm` / `arm64` / `x86` / `x86_64`):

| File | Description |
|------|-------------|
| `florida-server-<ver>-android-<arch>.gz` | frida-server (push to device) |
| `florida-gadget-<ver>-android-<arch>.so.gz` | frida-gadget (embed in APK) |
| `florida-inject-<ver>-android-<arch>.gz` | frida-inject (inject into process) |
| `florida-gumjs-<ver>-android-<arch>.a.gz` | frida-gumjs static lib (link in NDK) |

## Use frida-server

```bash
# Push to device
adb push florida-server-*.gz /data/local/tmp/
adb shell "gunzip /data/local/tmp/florida-server-*.gz"
adb shell "mv /data/local/tmp/florida-server-* /data/local/tmp/florida-server"
adb shell "chmod 755 /data/local/tmp/florida-server"

# Run (root required)
adb shell "/data/local/tmp/florida-server -D"
```

## Use frida-gadget

```bash
# Decompress and rename
gunzip florida-gadget-*.so.gz
mv florida-gadget-*.so libfrida-gadget.so

# Embed in APK (put in jniLibs/<abi>/)
# Then add to AndroidManifest.xml or load via System.loadLibrary()
```

## Use frida-client

Connect with standard frida-tools using Florida's obfuscated frida-server:

```bash
pip install frida-tools
frida-ps -H 127.0.0.1:27042  # after adb forward tcp:27042 tcp:27042
```
