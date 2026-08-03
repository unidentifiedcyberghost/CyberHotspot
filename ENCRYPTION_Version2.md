# Hardening & Obfuscation Guide

Goal: make source harder to copy while preserving legitimate distribution. There is no guaranteed "unbreakable" protection for Python. These steps raise the bar.

Strategy overview
1. Identify critical modules you want to protect (e.g., proprietary algorithms).
2. Compile those modules with Cython to native extensions (.so).
3. Use PyInstaller to bundle the app into a single executable.
4. Optionally obfuscate bytecode with PyArmor.
5. Distribute compiled binaries (ELF) rather than raw source.

Step-by-step (example)

A. Cythonize selected modules
- Mark files to protect, e.g. cyberhotspot/protected/*.py
- Create setup_cython.py:
  from setuptools import setup
  from Cython.Build import cythonize

  setup(
    ext_modules = cythonize(["cyberhotspot/protected/*.py"], compiler_directives={'language_level' : "3"})
  )
- Build:
  python3 -m pip install cython
  python3 setup_cython.py build_ext --inplace

B. Build a single-file executable with PyInstaller
- Install:
  python3 -m pip install pyinstaller
- Build:
  pyinstaller --onefile --name CyberHotspot_bin cyberhotspot/cli.py
- The dist/CyberHotspot_bin file is a self-contained executable. Combine with compiled .so files.

C. Obfuscation with PyArmor (optional)
- Install: python3 -m pip install pyarmor
- Obfuscate:
  pyarmor obfuscate -O dist_obf cyberhotspot/
- PyArmor adds a runtime wrapper and obfuscated .pyc files. Not foolproof, but increases complexity.

D. CI: Build on GitHub Actions
- Set up a workflow that runs Cythonize -> PyInstaller -> artifact upload.
- Keep secrets off-repo.

Legal & Ethical note
- Obfuscation should not be used to hide malware or violate law. Always respect users' rights and open-source licenses if you include third-party code.

Limitations
- Determined attackers can reverse PyInstaller and extract bytecode. Combining multiple layers (Cython + PyInstaller + PyArmor) makes reverse engineering more challenging but not impossible.
- For absolute protection, keep sensitive logic on a server you control and let clients be thin front-ends.
