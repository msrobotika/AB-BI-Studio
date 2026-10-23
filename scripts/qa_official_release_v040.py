#!/usr/bin/env python3
"""Verify official AB-BI v0.4.0 SOURCE release, SHA256 and first localhost import.
This ZIP is NOT a native standalone EXE and REQUIRES Python + pip.
No user data, no industrial hardware, no external services beyond package install.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
import venv
from urllib.request import Request, urlopen
import zipfile

FILE="AB_BI_Studio_v0_4_COMPLETO.zip"
HASH="AB_BI_Studio_v0_4_COMPLETO.sha256"

def verify_assets(assets):
    file=assets/FILE
    manifest=assets/HASH
    assert file.is_file() and manifest.is_file(), "No se han descargado los dos artefactos oficiales"
    line=manifest.read_text(encoding="ascii").strip()
    parsed=re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?(\S+)",line)
    assert parsed and parsed.group(2)==FILE, "SHA256 no describe el ZIP publicado"
    with file.open("rb") as f:
        actual=hashlib.file_digest(f,"sha256").hexdigest()
    assert parsed.group(1).lower()==actual, "SHA-256 del ZIP no coincide"
    return actual

def extract_release(archive,destination):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, "ZIP corrupto (CRC)"
        names=z.namelist()
        assert len(names)==len(set(names)) and names, "Entradas duplicadas/vacías"
        for name in names:
            p=Path(name)
            assert not p.is_absolute() and ".." not in p.parts, "Ruta ZIP insegura"
            assert p.parts[0]=="AB_BI_Studio_v0_4", "Prefijo de release incorrecto"
        z.extractall(destination)
    root=destination/"AB_BI_Studio_v0_4"
    files={"requirements.txt","constraints.txt","run.py","iniciar.bat",
           "iniciar.sh","LICENSE","MANIFEST.sha256","examples/datos_para_limpiar.csv"}
    assert all((root/x).is_file() for x in files), "ZIP carece de arranque, dataset o licencia"
    expected={}
    for line in (root/"MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest,filename=line.split("  ",1)
        assert re.fullmatch("[0-9a-f]{64}",digest), "Manifest inválido"
        assert not filename.startswith("/") and ".." not in Path(filename).parts
        expected[filename]=digest
    assert len(expected)>=15
    for filename, digest in expected.items():
        file=root/filename
        assert file.is_file(), "El fichero declarado falta: "+filename
        with file.open("rb") as f: actual=hashlib.file_digest(f,"sha256").hexdigest()
        assert actual==digest, "Manifest alterado: "+filename
    return root,len(expected)

def http(origin,path,body=None,content_type=None):
    headers={}
    if content_type:headers["Content-Type"]=content_type
    req=Request(origin+path,method="POST" if body is not None else "GET",
                data=body,headers=headers)
    with urlopen(req,timeout=8) as r:
        return r.status,r.read()

def check_runtime(root,work):
    virtual=work/"venv"
    venv.EnvBuilder(with_pip=True).create(virtual)
    exe=virtual/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    pip=subprocess.run([str(exe),"-m","pip","install",
       "--disable-pip-version-check","-r","requirements.txt"],
       cwd=root,capture_output=True,text=True,timeout=150)
    assert pip.returncode==0, "Dependencias de release no se instalan: "+pip.stderr[-600:]
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1",0))
        port=probe.getsockname()[1]
    log=work/"bi-server.log"
    with log.open("w",encoding="utf-8",errors="replace") as stream:
        env={**os.environ,"AB_BI_PORT":str(port),
             "BROWSER":"true","PYTHONDONTWRITEBYTECODE":"1"}
        process=subprocess.Popen([str(exe),"run.py"],cwd=root,
             env=env,stdout=stream,stderr=subprocess.STDOUT)
        origin="http://127.0.0.1:"+str(port)
        try:
            ready=False
            until=time.monotonic()+40
            while time.monotonic()<until:
                if process.poll() is not None:
                    raise RuntimeError("BI terminó antes de arrancar: "+log.read_text(errors="replace")[-400:])
                try:
                    status,body=http(origin,"/api/health")
                    if status==200 and json.loads(body).get("version")=="0.4.0":
                        ready=True
                        break
                except (OSError,ValueError):pass
                time.sleep(.25)
            assert ready,"AB-BI v0.4.0 no respondió en localhost"
            status,html=http(origin,"/")
            assert status==200 and b"AB" in html, "Frontend BI no se sirvió"
            sample=(root/"examples"/"datos_para_limpiar.csv").read_bytes()
            boundary=b"ABBIQA20261023"
            payload=(b"--"+boundary+b"\r\n"+
              b'Content-Disposition: form-data; name="file"; filename="datos_para_limpiar.csv"\r\n'+
              b"Content-Type: text/csv\r\n\r\n"+sample+b"\r\n--"+boundary+b"--\r\n")
            status,result=http(origin,"/api/import",payload,
                 "multipart/form-data; boundary="+boundary.decode())
            uploaded=json.loads(result)
            assert status==200 and uploaded.get("added"),"Falló importación CSV"
            table=uploaded["added"][0]
            _,frame=http(origin,"/api/table/"+table+"?limit=30")
            frame=json.loads(frame)
            assert frame["total"]==4, "Importación CSV distinta de las cuatro filas de ejemplo"
            assert {"Nombre","Importe","Fecha","Grupo"}.issubset(frame["rows"][0]),"Columnas incorrectas"
            status,report=http(origin,"/api/profile/"+table)
            assert status==200 and json.loads(report).get("rows")==4
            status,model=http(origin,"/api/model")
            assert status==200 and any(t["name"]==table for t in json.loads(model)["tables"])
            return {"api_health":"PASS","frontend":"PASS",
                    "csv_import_rows":frame["total"],"columns_verified":4,
                    "profile":"PASS","model":"PASS"}
        finally:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=10)

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--assets-dir",type=Path,required=True)
    args=parser.parse_args()
    digest=verify_assets(args.assets_dir)
    with tempfile.TemporaryDirectory(prefix="abbi-official-qa-",
                                      ignore_cleanup_errors=True) as temp:
        work=Path(temp)
        root,count=extract_release(args.assets_dir/FILE,work/"extracted")
        result=check_runtime(root,work)
    print(json.dumps({"release":"v0.4.0","kind":"SOURCE_ZIP_NOT_EXE",
       "sha256":digest,"zip_manifest_entries":count,"platform":sys.platform,
       **result},ensure_ascii=False))
    print("PASS: descargado ZIP oficial, SHA256, instalación Python nueva, HMI y CSV→modelo")

if __name__=="__main__":main()
