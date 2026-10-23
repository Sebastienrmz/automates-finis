"""Construire une version Windows de démonstration avec PyInstaller."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
    '--onedir', '--console', '--name', 'Automates-finis', str(root / 'main.py')],
    cwd=root, check=True)
folder = root / 'dist/Automates-finis'
shutil.copytree(root / 'data', folder / 'data', dirs_exist_ok=True)
shutil.copyfile(root / 'README.md', folder / 'README.md')
(folder / 'Tester.bat').write_text(
    '@echo off\nchcp 65001 >nul\ncd /d "%~dp0"\n"Automates-finis.exe"\npause\n', encoding='utf-8')
# Vérifier aussi l’exécutable empaqueté : alphabet vide puis exemple et reconnaissance.
for number, answers in [('01', 'o\n\nfin\n2\nn\n'),
                         ('exemple', 'o\no\nabaa\naba\nfin\n2\nn\n')]:
    result = subprocess.run([str(folder / 'Automates-finis.exe')],
        input=number + '\n' + answers, text=True, encoding='utf-8',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root.parent,
        timeout=45, check=True)
    if result.stderr or 'Erreur de lecture' in result.stdout or 'Traceback' in result.stdout:
        raise RuntimeError(result.stdout + result.stderr)
    if 'MINIMISATION' not in result.stdout:
        raise RuntimeError('Parcours de démonstration incomplet')
    if number == 'exemple' and not ("'abaa' est ACCEPTÉ" in result.stdout
                                  and "'aba' est REFUSÉ" in result.stdout):
        raise RuntimeError('Résultat de reconnaissance incorrect')
shutil.make_archive(str(root / 'dist/Automates-finis-Windows'), 'zip',
    root_dir=folder.parent, base_dir=folder.name)
print('Version Windows construite et essayée.')
