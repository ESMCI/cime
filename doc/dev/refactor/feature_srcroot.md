# Feature: SRCROOT Standardization

Remove `config_files.xml` indirection and standardize SRCROOT resolution for submodule usage.

## Changes

### SRCROOT Resolution Priority
1. Environment variable `SRCROOT`
2. User config `~/.cime/config`
3. Command-line flag `--srcroot`
4. Step up one directory from CIMEROOT
5. CIMEROOT itself (standalone mode)

### What's Removed
- `CIME/data/config/{e3sm,cesm,ufs}/config_files.xml`
- `MODEL_CONFIG_FILES` indirection
- Model-specific `get_config_path()` logic

### What's Added
- `CIME/core/config/srcroot.py` - SRCROOT resolver with DI
- `CIME/core/config/loader.py` - Direct config file loader
- `--srcroot` flag to CLI tools
- Standalone mode for unit testing

### Expected Directory Structure
```
$SRCROOT/
├── cime_config/           # Model config (validated)
│   ├── config_grids.xml
│   ├── config_compsets.xml
│   ├── config_machines.xml
│   └── config_tests.xml
└── cime/                  # CIME submodule
```

## Implementation (DI-Compliant)

### SRCROOTResolver
```python
class SRCROOTResolver:
    """Resolves SRCROOT with dependency injection."""
    
    def __init__(self, cimeroot: Path, filesystem: FileSystem, 
                 environment: EnvironmentProvider, user_config: UserConfigProvider):
        # All dependencies injected
        
    def resolve(self, flag_value: Optional[str] = None) -> SRCROOTResolution:
        # Priority: env > user_config > flag > implicit
        # Returns: SRCROOTResolution(path, source, standalone_mode)
```

**DI Pattern**: Constructor injection, no globals, fully testable with mocks.

### ConfigFileLoader
```python
class ConfigFileLoader:
    """Loads config files from $SRCROOT/cime_config with DI."""
    
    def __init__(self, srcroot: Path, filesystem: FileSystem):
        # Filesystem injected for testability
        
    def validate_and_load(self, require_full: bool = True) -> ConfigFiles:
        # Validates cime_config exists
        # Returns: ConfigFiles(paths to all config XMLs)
```

**DI Pattern**: Uses injected FileSystem, no direct path.is_dir() calls.

### Factory Functions
```python
def create_srcroot_resolver(...) -> SRCROOTResolver:
    # Provides defaults for production, allows injection for tests
    
def create_config_loader(...) -> ConfigFileLoader:
    # Provides defaults for production, allows injection for tests
```

## Testing

**Mock-based testing** (no global state, no real filesystem):

```python
def test_srcroot_from_environment():
    mock_env = MockEnvironment({"SRCROOT": "/test"})
    mock_fs = MockFileSystem({Path("/test/cime_config")})
    
    resolver = SRCROOTResolver(cimeroot, mock_fs, mock_env, mock_config)
    resolution = resolver.resolve()
    
    assert resolution.path == Path("/test")
    assert resolution.source == "environment"
```

## Migration

**4-Stage Rollout:**
1. **Opt-in** (Weeks 1-2): Feature flag `CIME_USE_NEW_CONFIG_LOADER=true`
2. **Opt-out** (Weeks 3-4): New system default, old available via flag
3. **Deprecation**: Warnings on old code paths
4. **Removal**: Delete old config_files.xml system

## Integration with Refactor

- **Uses Slice 1**: FileSystem, EnvironmentProvider abstractions
- **New Slice 3A**: SRCROOT standardization (3-4 weeks)
- **Before Slice 3B**: Must complete before build system refactor

## Validation

- E3SM case creation workflow
- CESM case creation workflow
- NorESM case creation workflow
- Standalone mode for unit tests

## Benefits

- Simpler config loading (no indirection)
- Better error messages (fail early)
- Fully testable (DI throughout)
- Explicit standalone mode
- Deterministic SRCROOT resolution
