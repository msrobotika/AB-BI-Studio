"""Launch this local application, without accidentally opening an older instance."""
import json
import os
import socket
import threading
import time
import urllib.request
import webbrowser
import uvicorn

HOST='127.0.0.1'

def choose_port():
    requested=os.environ.get('AB_BI_PORT')
    ports=[int(requested)] if requested else range(8765,8785)
    for port in ports:
        if not 1024<=port<=65535:
            raise ValueError('AB_BI_PORT debe estar entre 1024 y 65535')
        with socket.socket() as probe:
            try:probe.bind((HOST,port))
            except OSError:continue
            return port
    raise OSError('No se ha encontrado un puerto libre. Cierra otra instancia o indica AB_BI_PORT.')

def open_when_ready(port):
    url=f'http://{HOST}:{port}'
    for _ in range(100):
        try:
            with urllib.request.urlopen(url+'/api/health',timeout=.5) as response:
                health=json.load(response)
                if health.get('version')=='0.4.0':
                    webbrowser.open(url)
                    return
        except (OSError,ValueError):
            time.sleep(.2)
    print(f'Abre el navegador en {url} cuando el motor esté listo.')

if __name__=='__main__':
    try:port=choose_port()
    except (OSError,ValueError) as exc:
        print(str(exc));raise SystemExit(1)
    print(f'AB-BI Studio 0.4: http://{HOST}:{port}',flush=True)
    threading.Thread(target=open_when_ready,args=(port,),daemon=True).start()
    uvicorn.run('backend.server:app',host=HOST,port=port,log_level='warning')
