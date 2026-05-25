# Florida - Build Guide

## Files Included

```
patches/
  frida-core/
    apply.py          # 自动应用所有反检测修改
    *.patch            # 备用 (apply.py 已涵盖)
  frida-gum/
    0001-Florida-pool-frida.patch
```

## Requirements

- Ubuntu 22.04 x86_64
- Android NDK r25 或 r29
- Python 3.9+ / pip (lief, graphlib)
- JDK 17

```bash
sudo apt-get install build-essential ninja-build gcc-multilib g++-multilib \
  lib32stdc++-9-dev flex bison ruby ruby-dev python3-requests \
  python3-setuptools python3-dev python3-pip libc6-dev libc6-dev-i386 -y
sudo gem install fpm -v 1.11.0 --no-document
pip install lief graphlib
```

## Build

```bash
# 1. Clone frida
git clone --recurse-submodules https://github.com/frida/frida
cd frida

# 2. Checkout desired version
git fetch --tags
git checkout -f tags/17.9.10
git submodule update --init --recursive
cd ..

# 3. Apply Florida patches
python3 patches/frida-core/apply.py

# 4. frida-gum patch (16.x: cd frida/frida-gum, 17.x: cd frida/subprojects/frida-gum)
cd frida/subprojects/frida-gum
git am ../../patches/frida-gum/*.patch
cd ../..

# 5. Build for Android (4 arches)
export ANDROID_NDK_ROOT=/path/to/ndk
for ARCH in android-arm android-arm64 android-x86 android-x86_64; do
  mkdir build-$ARCH && cd build-$ARCH
  ../frida/configure --host=$ARCH && make
  cd ..
done
```

## Output

```
build-android-arm/subprojects/frida-core/server/frida-server
build-android-arm64/subprojects/frida-core/server/frida-server
build-android-x86/subprojects/frida-core/server/frida-server
build-android-x86_64/subprojects/frida-core/server/frida-server

build-android-*/subprojects/frida-core/inject/frida-inject
build-android-*/subprojects/frida-core/lib/gadget/frida-gadget.so
```

## Notes

- frida >= 17.8.1 用 NDK r29, < 17.8.1 用 NDK r25
- frida >= 17.0 子模块在 `frida/subprojects/`, 16.x 在 `frida/` 根目录
- apply.py 自动处理两种目录结构, 不匹配的修改会打印 WARN 跳过
