# Acquila ZMQ Library - Project Structure

## Directory Structure

```
zmq_communication/
├── acquila_zmq/              # Main library package
│   └── __init__.py           # Library code with AcquilaServer & AcquilaClient
├── examples/                 # Example scripts
│   ├── run_server.py         # Start the message relay server
│   ├── example_motor.py      # Example component with feedback
│   └── run_script_example.py # Example script sending commands
├── .git/                     # Git repository
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
├── MANIFEST.in               # Package manifest for distribution
├── pyproject.toml            # Modern Python package configuration
├── QUICKSTART.md             # Quick reference for immediate use
├── README.md                 # Main documentation
├── requirements.txt          # Dependencies (pyzmq)
├── setup.py                  # Setup script (delegates to pyproject.toml)
├── test_installation.py      # Test script to verify installation
└── USAGE.md                  # Comprehensive usage guide

# Old files (ignored by git, kept for reference):
├── acquila_zmq.py            # Old standalone version
├── example_motor.py          # Duplicate
├── run_script_example.py     # Duplicate
└── run_server.py             # Duplicate
```

## What Changed

### Before (Simple Scripts)
- Single file `acquila_zmq.py` with all code
- Example files scattered in root directory
- No proper packaging
- Hard to import in other projects

### After (Proper Library)
- Organized package structure (`acquila_zmq/`)
- Modern Python packaging (pyproject.toml)
- Proper version management
- Easy to install and import
- Comprehensive documentation
- MIT License
- Test script included

## How to Use in Your Projects

### 1. Install Once
```bash
# In your 3dviewer project
cd c:\code\antigravity\3dviewer
pip install -e c:\code\antigravity\zmq_communication

# In your 3drecon project
cd c:\code\antigravity\3drecon
pip install -e c:\code\antigravity\zmq_communication
```

### 2. Import Anywhere
```python
from acquila_zmq import AcquilaServer, AcquilaClient

# Use it!
server = AcquilaServer()
client = AcquilaClient()
```

### 3. Make Changes
Any changes you make to the library code in `c:\code\antigravity\zmq_communication`
will immediately be available in all projects that installed it with `-e` flag.

## Key Files

| File | Purpose |
|------|---------|
| `acquila_zmq/__init__.py` | Main library code |
| `pyproject.toml` | Package configuration |
| `README.md` | Overview and installation |
| `USAGE.md` | Detailed usage examples |
| `QUICKSTART.md` | Quick reference |
| `test_installation.py` | Verify installation works |
| `examples/` | Working example scripts |

## Next Steps

1. ✓ Library is properly structured
2. ✓ Git repository is committed
3. ✓ Installation tested and working
4. → Install in 3dviewer project
5. → Install in 3drecon project
6. → Start integrating ZMQ communication

## Testing

Run the test script to verify everything works:
```bash
cd c:\code\antigravity\zmq_communication
python test_installation.py
```

You should see:
```
✓ Import successful! Version: 1.0.0
✓ Communication test PASSED!
✓ All tests PASSED!
```

## Documentation Files

- **README.md** - Start here for overview
- **QUICKSTART.md** - For immediate use
- **USAGE.md** - For detailed examples and integration patterns
- **This file** - For understanding the project structure

## Version

Current version: **1.0.0**

Defined in:
- `acquila_zmq/__init__.py` (`__version__`)
- `pyproject.toml` (`version`)
