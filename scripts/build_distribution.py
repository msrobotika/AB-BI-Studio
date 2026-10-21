"""Build an allowlisted source ZIP and verify its bytes and checksums."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TOP_FILES={'README.md','LICENSE','THIRD_PARTY_NOTICES.md','CHANGELOG.md','CONTRIBUTING.md',
           'SECURITY.md','EMPEZAR_AQUI.txt','requirements.txt','requirements-dev.txt',
           'constraints.txt','run.py','iniciar.bat','iniciar.sh','.gitignore'}
DIRECTORIES={'backend','frontend','tests','docs','examples','scripts','third_party','.github'}
EXCLUDE={'__pycache__','.pytest_cache','.venv','data','.git','dist'}


def build(output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    entries={}
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.is_symlink():continue
        relative=path.relative_to(ROOT)
        if any(part in EXCLUDE for part in relative.parts):continue
        if len(relative.parts)==1 and path.name not in TOP_FILES:continue
        if len(relative.parts)>1 and relative.parts[0] not in DIRECTORIES:continue
        if path.suffix in ('.pyc','.abbi') or path.name.startswith('.env'):continue
        entries[relative.as_posix()]=path.read_bytes()
    manifest=''.join(hashlib.sha256(blob).hexdigest()+'  '+name+'\n' for name,blob in entries.items())
    entries['MANIFEST.sha256']=manifest.encode('utf-8')
    archive=output/'AB_BI_Studio_v0_4_COMPLETO.zip'
    prefix='AB_BI_Studio_v0_4/'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,blob in entries.items():
            info=zipfile.ZipInfo(prefix+name,date_time=(2026,10,21,0,0,0))
            info.create_system=3
            info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,blob)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise RuntimeError('ZIP CRC failed')
        for name,blob in entries.items():
            if z.read(prefix+name)!=blob:raise RuntimeError('Archive mismatch: '+name)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum=output/'AB_BI_Studio_v0_4_COMPLETO.sha256'
    checksum.write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    print(archive)
    print(digest)
    print(str(len(entries))+' files; '+str(archive.stat().st_size)+' bytes; CRC OK')
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    build(parser.parse_args().output)
