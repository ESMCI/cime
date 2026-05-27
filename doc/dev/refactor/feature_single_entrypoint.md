# Feature: Single CIME Entrypoint

Collapse all symlinked case scripts into one `cime` entrypoint with shell wrappers.

## Changes

### Current: ~20 Symlinks
```
case_dir/
├── case.setup -> /path/to/CIME/scripts/Tools/case.setup
├── case.build -> /path/to/CIME/scripts/Tools/case.build
├── xmlchange -> /path/to/CIME/scripts/Tools/xmlchange
└── ... (~17 more symlinks)
```

**Problem**: Changing CIME version requires updating all symlinks.

### New: 1 Symlink + Shell Wrappers
```
case_dir/
├── cime -> /path/to/CIME/scripts/cime     # Only symlink
├── case.setup                              # Wrapper script
├── case.build                              # Wrapper script
├── xmlchange                               # Wrapper script
└── ...
```

**Benefit**: Change CIME version by updating one symlink.

## Implementation

### Single Entrypoint: `CIME/scripts/cime`

```python
#!/usr/bin/env python3
"""Single entrypoint for all CIME case operations."""

COMMANDS = {
    'case.setup': 'CIME.Tools.case_setup',
    'case.build': 'CIME.Tools.case_build',
    'xmlchange': 'CIME.Tools.xmlchange',
    # ... all tools
}

def main():
    command = sys.argv[1]
    module = __import__(COMMANDS[command], fromlist=['main'])
    sys.argv = [f"cime {command}"] + sys.argv[2:]
    return module.main()
```

### Shell Wrapper Template

```bash
#!/usr/bin/env bash
# Wrapper for: cime case.setup
exec "$(dirname "$0")/cime" case.setup "$@"
```

**Key**: 
- `exec` replaces shell (clean exit codes)
- `"$@"` preserves all arguments
- Finds `cime` relative to wrapper

### Case Setup

```python
def create_case_scripts(case_root: Path, cimeroot: Path):
    # Create single cime symlink
    (case_root / "cime").symlink_to(cimeroot / "scripts" / "cime")
    
    # Create shell wrappers
    wrapper = '#!/usr/bin/env bash\nexec "$(dirname "$0")/cime" {cmd} "$@"\n'
    
    for tool in ["case.setup", "case.build", "xmlchange", ...]:
        path = case_root / tool
        path.write_text(wrapper.format(cmd=tool))
        path.chmod(0o755)
```

## Migration

### New Cases
Immediately use new pattern (single symlink + wrappers).

### Existing Cases
**Option 1**: Leave unchanged - both patterns work  
**Option 2**: Provide upgrade utility (optional)

**No breaking changes** - old and new patterns coexist.

## Benefits

1. **Simple CIME updates**: Change one symlink instead of ~20
2. **Cleaner case dirs**: One symlink vs. many
3. **Clear CIME version**: Easy to see which CIME in use
4. **Better portability**: Fewer symlinks to manage
5. **CLI foundation**: Natural path to full CLI layer

## Testing

- Command routing and argument passing
- All major case operations
- Old and new case patterns
- Exit codes and output

## Integration with Refactor

- **Uses**: Slice 1 bootstrap (`ensure_cime_on_path`)
- **Enables**: Future CLI layer (optional)
- **Timeline**: 2-3 weeks, can run parallel with other slices

## Future Enhancements

### Subcommands (optional)
```bash
cime case setup          # Alternative syntax
cime xml change VAR=val
```

### Global Options (optional)
```bash
cime --case /path case.build
cime --verbose case.setup
cime --help
```

## Decision Points

1. **Existing cases**: Auto-upgrade or leave unchanged?
   - Recommend: Leave unchanged (safer)

2. **Wrapper language**: Shell or Python?
   - Recommend: Shell (simpler, minimal overhead)

3. **Command syntax**: Keep dots (`case.setup`)?
   - Recommend: Keep dots (backward compatible)
