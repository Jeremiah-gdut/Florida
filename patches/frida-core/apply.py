#!/usr/bin/env python3
"""Apply Florida anti-detection modifications to frida-core submodule."""
import os, sys, re

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(base, '..', '..'))
frida_core = os.path.join(root, 'frida', 'subprojects', 'frida-core')

def filepath(rel):
    return os.path.join(frida_core, rel)

def read(path):
    with open(path, 'r') as f:
        return f.read()

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

def replace(path, old, new):
    content = read(path)
    if old not in content:
        print(f"  WARN: pattern not found in {path}")
        return False
    content = content.replace(old, new)
    write(path, content)
    print(f"  OK: {path}")
    return True

def regex_replace(path, pattern, repl):
    content = read(path)
    new_content, n = re.subn(pattern, repl, content)
    if n == 0:
        print(f"  WARN: regex not matched in {path}")
        return False
    write(path, new_content)
    print(f"  OK: {path} ({n} matches)")
    return True

def insert_after(path, marker, lines):
    content = read(path)
    if marker not in content:
        print(f"  WARN: marker not found in {path}")
        return False
    idx = content.index(marker) + len(marker)
    # find end of line
    end = content.index('\n', idx)
    new_content = content[:end+1] + lines + content[end+1:]
    write(path, new_content)
    print(f"  OK: {path}")
    return True

print("Applying Florida patches to frida-core...")

# ============================================================
# Patch 0001: string_frida_rpc
# Add getRpcStr() method and obfuscate "frida:rpc" strings
# ============================================================
print("\n[0001] string_frida_rpc")

rp = filepath('lib/base/rpc.vala')
get_rpc_str = '''
\t\tpublic string getRpcStr(bool quote){
\t\t\tstring result = (string) GLib.Base64.decode((string) GLib.Base64.decode("Wm5KcFpHRTZjbkJq"));
\t\t\tif(quote){
\t\t\t\treturn "\\"" + result + "\\"";
\t\t\t}else{
\t\t\t\treturn result;
\t\t\t}
\t\t}
'''

if os.path.exists(rp):
    c = read(rp)
    # Insert getRpcStr BEFORE the 'call' method, not inside the constructor
    # The 'async Json.Node call' method follows the constructor at class level
    marker = None
    for pat in ['public async Json.Node call (', 'public async GLib.Json.Node call (']:
        if pat in c:
            marker = pat
            break
    if marker is None:
        print("  WARN: could not find call() method in rpc.vala, patch 0001 skipped")
    else:
        idx = c.index(marker)
        # Insert before this line
        c = c[:idx] + get_rpc_str + '\n' + c[idx:]
        write(rp, c)

        # Replace frida:rpc references
        replace(rp, '".add_string_value ("frida:rpc")', '".add_string_value (getRpcStr(false))')
        replace(rp, 'json.index_of ("\\"frida:rpc\\"")', 'json.index_of (getRpcStr(true))')
        c = read(rp)
        if 'type != "frida:rpc"' in c:
            c = c.replace('type != "frida:rpc"', 'type != getRpcStr(false)')
            write(rp, c)
            print("  OK: frida:rpc type check")
        print("  OK: lib/base/rpc.vala")
else:
    print(f"  SKIP: {rp} not found")

# ============================================================
# Patch 0002: frida_agent_so
# Randomize agent file names
# ============================================================
print("\n[0002] frida_agent_so")

lh = filepath('src/linux/linux-host-session.vala')
if os.path.exists(lh):
    c = read(lh)
    # Insert random_prefix before agent = new AgentDescriptor
    marker = 'agent = new AgentDescriptor (PathTemplate ("frida-agent-<arch>.so"'
    if marker in c:
        c = c.replace(
            marker,
            'var random_prefix = GLib.Uuid.string_random();\n\t\t\t' + marker.replace('frida-agent-<arch>.so"', 'random_prefix + "-<arch>.so"')
        )
        # Replace resource names
        c = c.replace(
            'new AgentResource ("frida-agent-arm.so"',
            'new AgentResource (random_prefix + "-arm.so"'
        )
        c = c.replace(
            'new AgentResource ("frida-agent-arm64.so"',
            'new AgentResource (random_prefix + "-arm64.so"'
        )
        write(lh, c)
        print("  OK: src/linux/linux-host-session.vala")
    else:
        print("  WARN: marker not found, trying alt pattern")
        # Fallback: use regex
        if re.search(r'agent = new AgentDescriptor \(PathTemplate \("frida-agent-<arch>\.so"\)', c):
            c = re.sub(
                r'agent = new AgentDescriptor \(PathTemplate \("frida-agent-<arch>\.so"\)',
                'var random_prefix = GLib.Uuid.string_random();\n\t\t\tagent = new AgentDescriptor (PathTemplate (random_prefix + "-<arch>.so")',
                c
            )
            c = c.replace('"frida-agent-arm.so"', 'random_prefix + "-arm.so"')
            c = c.replace('"frida-agent-arm64.so"', 'random_prefix + "-arm64.so"')
            write(lh, c)
            print("  OK: src/linux/linux-host-session.vala (fallback)")
        else:
            print("  WARN: could not find agent descriptor pattern")
else:
    print(f"  SKIP: {lh} not found")

# ============================================================
# Patch 0003: symbol_frida_agent_main
# Rename frida_agent_main to main in all Vala files
# ============================================================
print("\n[0003] symbol_frida_agent_main")

for dirpath, dirnames, filenames in os.walk(frida_core):
    for fn in filenames:
        if fn.endswith('.vala'):
            fp = os.path.join(dirpath, fn)
            c = read(fp)
            if '"frida_agent_main"' in c:
                c = c.replace('"frida_agent_main"', '"main"')
                write(fp, c)
                print(f"  OK: {os.path.relpath(fp, frida_core)}")

# Create anti-anti-frida.py
anti_frida = filepath('src/anti-anti-frida.py')
anti_frida_content = '''import lief
import sys
import random
import os

def log_color(msg):
    print(f"\\033[1;31;40m{msg}\\033[0m")

if __name__ == "__main__":
    input_file = sys.argv[1]
    random_charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    log_color(f"[*] Patch frida-agent: {input_file}")
    binary = lief.parse(input_file)

    if not binary:
        log_color(f"[*] Not elf, exit")
        exit()

    random_name = "".join(random.sample(random_charset, 5))
    log_color(f"[*] Patch `frida` to `{random_name}`")

    for symbol in binary.symbols:
        if symbol.name == "frida_agent_main":
            symbol.name = "main"

        if "frida" in symbol.name:
            symbol.name = symbol.name.replace("frida", random_name)

        if "FRIDA" in symbol.name:
            symbol.name = symbol.name.replace("FRIDA", random_name)

    all_patch_string = ["FridaScriptEngine", "GLib-GIO", "GDBusProxy", "GumScript"]
    for section in binary.sections:
        if section.name != ".rodata":
            continue
        for patch_str in all_patch_string:
            addr_all = section.search_all(patch_str)
            for addr in addr_all:
                patch = [ord(n) for n in list(patch_str)[::-1]]
                log_color(f"[*] Patching section name={section.name} offset={hex(section.file_offset + addr)} orig:{patch_str} new:{''.join(list(patch_str)[::-1])}")
                binary.patch_address(section.file_offset + addr, patch)

    binary.write(input_file)

    # thread_gum_js_loop
    random_name = "".join(random.sample(random_charset, 11))
    log_color(f"[*] Patch `gum-js-loop` to `{random_name}`")
    os.system(f"sed -b -i s/gum-js-loop/{random_name}/g {input_file}")

    # thread_gmain
    random_name = "".join(random.sample(random_charset, 5))
    log_color(f"[*] Patch `gmain` to `{random_name}`")
    os.system(f"sed -b -i s/gmain/{random_name}/g {input_file}")

    # thread_gdbus
    random_name = "".join(random.sample(random_charset, 5))
    log_color(f"[*] Patch `gdbus` to `{random_name}`")
    os.system(f"sed -b -i s/gdbus/{random_name}/g {input_file}")

    log_color(f"[*] Patch Finish")
'''

os.makedirs(os.path.dirname(anti_frida), exist_ok=True)
write(anti_frida, anti_frida_content)
print(f"  OK: src/anti-anti-frida.py (created)")

# ============================================================
# Patch 0006: protocol_unexpected_command
# ============================================================
print("\n[0006] protocol_unexpected_command")

dc = filepath('src/droidy/droidy-client.vala')
if os.path.exists(dc):
    old = 'throw new Error.PROTOCOL ("Unexpected command");'
    new = 'break; // throw new Error.PROTOCOL ("Unexpected command");'
    replace(dc, old, new)
else:
    print(f"  SKIP: {dc} not found")

# ============================================================
# Patch 0008: pool-frida
# ============================================================
print("\n[0008] pool-frida")

fg = filepath('src/frida-glue.c')
if os.path.exists(fg):
    marker = 'g_io_module_openssl_register ();'
    insert_after(fg, marker, '\n    g_set_prgname ("ggbond");\n')
else:
    print(f"  SKIP: {fg} not found")

# ============================================================
# Patch 0009: memfd-name-jit-cache
# ============================================================
print("\n[0009] memfd-name-jit-cache")

lv = filepath('lib/base/linux.vala')
if os.path.exists(lv):
    old = 'Linux.syscall (LinuxSyscall.MEMFD_CREATE, name, flags)'
    new = 'Linux.syscall (LinuxSyscall.MEMFD_CREATE, "jit-cache", flags)'
    replace(lv, old, new)
else:
    print(f"  SKIP: {lv} not found")

# ============================================================
# Patch 0010: exec anti-anti-frida.py
# ============================================================
print("\n[0010] exec anti-anti-frida.py")

ea = filepath('src/embed-agent.py')
if os.path.exists(ea):
    c = read(ea)
    # Find the linux/android section and insert anti-anti-frida execution
    # Pattern: } else:\n{ws}embedded_agent.write_bytes(b"")\n{ws}embedded_assets += [embedded_agent]
    old_pattern = '''            else:
                embedded_agent.write_bytes(b"")
            embedded_assets += [embedded_agent]'''
    
    new_pattern = '''            else:
                embedded_agent.write_bytes(b"")
            import os
            custom_script=str(output_dir)+"/../../../../frida/subprojects/frida-core/src/anti-anti-frida.py"
            return_code = os.system("python3 "+custom_script+" "+str(priv_dir / f"frida-agent-{flavor}.so"))
            if return_code == 0:
                print("anti-anti-frida finished")
            else:
                print("anti-anti-frida error. Code:", return_code)
            
            embedded_assets += [embedded_agent]'''

    if old_pattern in c:
        c = c.replace(old_pattern, new_pattern, 1)
        write(ea, c)
        print("  OK: src/embed-agent.py")
    else:
        print("  WARN: pattern not found in embed-agent.py, patch 0010 skipped")
else:
    print(f"  SKIP: {ea} not found")

print("\nAll Florida patches applied.")
