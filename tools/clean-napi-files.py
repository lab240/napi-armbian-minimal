#!/usr/bin/env python3
"""Remove configured files from an Armbian image."""
import fnmatch
import os
from pathlib import Path
import sys


def prune(root, tree, apply, patterns):
    if not tree.resolve().is_relative_to(root) or tree.is_symlink():
        raise ValueError(f'Unsafe directory: {tree}')
    if not tree.exists():
        return []
    files, directories = {}, []
    for parent, dirs, names in os.walk(tree, followlinks=False):
        parent = Path(parent)
        for name in list(dirs):
            path = parent / name
            if path.is_symlink():
                # Preserve directory aliases without following them.
                dirs.remove(name)
            else:
                directories.append(path)
        for name in names:
            path = parent / name
            files[path.relative_to(tree).as_posix()] = path
    keep = {n for n in files if any(fnmatch.fnmatchcase(n, p) for p in patterns)}
    pending = list(keep)
    while pending:
        path = files[pending.pop()]
        if not path.is_symlink():
            continue
        target = path.resolve()
        if not target.is_relative_to(root):
            raise ValueError(f'Symlink escapes image: {path}')
        if target.is_relative_to(tree):
            name = target.relative_to(tree).as_posix()
            if name in files and name not in keep:
                keep.add(name)
                pending.append(name)
    remove = set(files) - keep
    size = sum(files[n].lstat().st_size for n in remove)
    print(f'{tree.relative_to(root)}: remove {len(remove)} files ({size / 1048576:.1f} MiB).')
    if not apply:
        return sorted(keep)
    for name in sorted(remove):
        files[name].unlink()
    for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        if not any(path.iterdir()):
            path.rmdir()
    return sorted(keep)


def clean(root, apply, kind, patterns):
    root = root.resolve(strict=True)
    if root == Path('/') or not (root / 'etc/armbian-release').is_file():
        raise ValueError('Expected an Armbian image root directory.')
    for p in patterns:
        if not p or p.startswith('/') or '..' in p.split('/') or '\n' in p:
            raise ValueError(f'Invalid pattern: {p}')
    rules = []
    if kind == 'docs':
        kept = prune(root, root / 'usr/share/doc', apply, patterns)
        rules = ['path-exclude=/usr/share/doc/*', 'path-include=/usr/share/doc/*/']
        rules += [f'path-include=/usr/share/doc/{p}' for p in patterns + kept]
    elif kind == 'dtbs':
        for tree in sorted((root / 'usr/lib').glob('linux-image-*')):
            # Restrict cleanup to kernel DTB trees.
            if tree.is_dir() and any(tree.rglob('*.dtb')):
                if not (tree / 'rockchip/rk3308-napi-c.dtb').is_file() and not (tree / 'rk3308-napi-c.dtb').is_file():
                    raise ValueError(f'NAPI-C DTB is missing: {tree}')
                prune(root, tree, apply, patterns)
        rules = ['path-exclude=/usr/lib/linux-image-*/*', 'path-include=/usr/lib/linux-image-*/*/']
        rules += [f'path-include=/usr/lib/linux-image-*/{p}' for p in patterns]
    elif kind == 'apt':
        prune(root, root / 'var/lib/apt/lists', apply, ['lock'])
    else:
        raise ValueError(f'Unknown cleanup: {kind}')
    if apply and rules:
        directory = root / 'etc/dpkg/dpkg.cfg.d'
        if not directory.resolve().is_relative_to(root):
            raise ValueError('Dpkg directory escapes image.')
        directory.mkdir(parents=True, exist_ok=True)
        config = directory / f'97-napi-{kind}'
        if config.is_symlink():
            raise ValueError('Dpkg configuration file is a symlink.')
        config.write_text('\n'.join(rules) + '\n')


if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[2] not in ('--apply', '--dry-run'):
        sys.exit('Usage: clean-napi-files.py ROOTFS --apply|--dry-run docs|dtbs|apt [PATTERN ...]')
    clean(Path(sys.argv[1]), sys.argv[2] == '--apply', sys.argv[3], sys.argv[4:])
