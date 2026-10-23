"""End-to-end tests against a real local HTTP server and Chromium."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import pytest
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def browser_page(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=os.environ.copy();env['ABBI_DATA_DIR']=str(tmp_path/'data')
    process=subprocess.Popen([sys.executable,'-m','uvicorn','backend.server:app','--host','127.0.0.1','--port',str(port),'--log-level','warning'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    url=f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError(process.stderr.read().decode())
            try:
                with urllib.request.urlopen(url+'/api/health',timeout=.3) as response:
                    if response.status==200:break
            except (OSError,ValueError):time.sleep(.1)
        else:raise RuntimeError('Local test server did not start')
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1500,'height':1100},device_scale_factor=1,accept_downloads=True)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url);expect(page.locator('.kpi')).to_have_count(4)
            yield page,url,errors
            browser.close()
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        process.stderr.close()


def select_columns(page,*names):
    page.locator('#cleanNone').click()
    for name in names:page.locator('#cleanColumns').get_by_text(name,exact=True).click()


def add_step(page,op,columns):
    select_columns(page,*columns);page.select_option('#cleanOperation',op);page.click('#addCleanStep')


def test_chart_themes_filters_and_explorer(browser_page):
    page,url,errors=browser_page
    docs=ROOT/'docs';docs.mkdir(exist_ok=True)
    donut=page.locator('.donut-svg')
    expect(donut.locator('.donut-segment')).to_have_count(2)
    assert donut.locator('.donut-segment').first.evaluate("el=>getComputedStyle(el).fill")=='none'
    assert donut.locator('.donut-segment').first.get_attribute('stroke')!=donut.locator('.donut-segment').nth(1).get_attribute('stroke')
    expect(page.locator('.legend-value small')).to_have_count(2)
    page.screenshot(path=str(docs/'ABBI_04_oscuro.png'),full_page=True)
    before=page.locator('.kpi strong').first.inner_text()
    page.locator('.legend-button').first.click()
    expect(page.locator('.filter-pill')).to_have_count(1)
    expect(page.locator('.kpi strong').first).not_to_have_text(before)
    page.click('#clearFilters');expect(page.locator('.kpi strong').first).to_have_text(before)
    page.select_option('#filterDimension','Equipos[Linea]');page.select_option('#filterOp','in')
    page.locator('#filterChoices').get_by_text('Línea 01',exact=True).click();page.locator('#filterChoices').get_by_text('Línea 02',exact=True).click();page.click('#applyFilter')
    expect(page.locator('.filter-pill')).to_have_count(1)
    page.select_option('#filterDimension','Lecturas[Produccion_kg]');page.select_option('#filterOp','between');page.select_option('#filterType','number')
    page.fill('#filterFrom','700');page.fill('#filterTo','900');page.click('#applyFilter');expect(page.locator('.filter-pill')).to_have_count(2)
    page.click('[data-view="data"]');page.select_option('#dataSort','Produccion_kg');page.select_option('#dataSortType','number');page.select_option('#dataSortDirection','desc')
    expect(page.locator('#dataInfo')).to_contain_text('de 504 filas')
    page.wait_for_timeout(350)
    rows=page.locator('#dataBody tr').all_text_contents();assert rows
    with page.expect_download() as download_info:page.click('#exportTableCsv')
    downloaded=download_info.value;downloaded.save_as(str(ROOT.parent/'filtered-test.csv'))
    text=Path(downloaded.path()).read_text(encoding='utf-8-sig');assert 'Produccion_kg' in text and len(text.splitlines())>1
    page.click('[data-view="measures"]');page.fill('#measureName','Prueba');page.fill('#daxSource','COUNTROWS(Lecturas)');page.click('#evaluateDax');expect(page.locator('#daxResult')).to_contain_text('RESULTADO')
    page.click('[data-view="dashboard"]');page.click('#clearFilters');expect(page.locator('.kpi strong').first).to_have_text(before)
    page.click('#themeToggle');expect(page.locator('html')).to_have_attribute('data-theme','light')
    assert donut.locator('.donut-segment').first.evaluate("el=>getComputedStyle(el).fill")=='none'
    page.screenshot(path=str(docs/'ABBI_04_claro.png'),full_page=True)
    page.reload();expect(page.locator('html')).to_have_attribute('data-theme','light');expect(page.locator('.kpi')).to_have_count(4)
    page.set_viewport_size({'width':390,'height':844});assert page.locator('#filterOp').bounding_box()['width']>250;page.screenshot(path=str(docs/'ABBI_04_movil.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    assert not errors,errors


def test_cleaning_preview_apply_undo_in_browser(browser_page):
    page,url,errors=browser_page;docs=ROOT/'docs'
    csv='Nombre;Importe;Fecha;Grupo\n  Ana  ;1.234,56;21/10/2026; A \n  Ana  ;1.234,56;21/10/2026; A \n Luis ;error;31/02/2026; B \n ;N/A;;\n'
    page.set_input_files('#uploadInput',{'name':'Limpieza_demo.csv','mimeType':'text/csv','buffer':csv.encode('utf-8')})
    expect(page.locator('#view-model')).to_be_visible();page.click('[data-view="clean"]');page.select_option('#cleanTable','Limpieza_demo')
    cols=['Nombre','Importe','Fecha','Grupo']
    add_step(page,'trim',cols)
    select_columns(page,'Importe');page.select_option('#cleanOperation','null_markers');page.fill('#cleanValue','N/A;');page.click('#addCleanStep')
    select_columns(page,'Importe');page.select_option('#cleanOperation','to_number');page.select_option('#cleanLocale','es');page.select_option('#cleanOnError','keep');page.click('#addCleanStep')
    select_columns(page,'Fecha');page.select_option('#cleanOperation','to_date');page.select_option('#cleanOnError','null');page.click('#addCleanStep')
    add_step(page,'deduplicate',cols);add_step(page,'drop_empty',cols)
    expect(page.locator('#cleanSteps li')).to_have_count(6)
    page.click('#previewClean');expect(page.locator('#applyClean')).to_be_enabled()
    expect(page.locator('#cleanPreview')).to_contain_text('2 conversiones no válidas')
    expect(page.locator('.diff-table')).to_contain_text('1234.56')
    response=page.request.get(url+'/api/table/Limpieza_demo');assert response.json()['total']==4
    page.screenshot(path=str(docs/'ABBI_04_limpieza.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2');page.screenshot(path=str(docs/'ABBI_04_limpieza_movil.png'),full_page=True)
    page.set_viewport_size({'width':1500,'height':1100})
    page.once('dialog',lambda dialog:dialog.accept());page.click('#applyClean');expect(page.locator('#cleanPreview')).to_contain_text('Limpieza aplicada')
    expect(page.locator('#undoClean')).to_be_enabled()
    result=page.request.get(url+'/api/table/Limpieza_demo').json();assert result['total']==2 and result['rows'][0]['Importe']==1234.56
    assert result['rows'][1]['Fecha'] is None
    with page.expect_download() as download_info:page.click('#saveExport')
    project=json.loads(Path(download_info.value.path()).read_text(encoding='utf-8'));assert project['cleaning_history'] and project['measures']['Producción total']
    page.once('dialog',lambda dialog:dialog.accept());page.click('#undoClean');expect(page.locator('#undoClean')).to_be_disabled()
    assert page.request.get(url+'/api/table/Limpieza_demo').json()['total']==4
    page.click('[data-view="profile"]');page.select_option('#profileTableSelect','Limpieza_demo');expect(page.locator('#qualitySummary')).to_contain_text('Filas duplicadas')
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    assert not errors,errors


def test_first_run_quickstart_guides_a_real_import(browser_page):
    """A first-time visitor can inspect the demo, import CSV and reach cleanup."""
    page, url, errors = browser_page
    expect(page.locator('#quickstart')).to_be_visible()
    expect(page.locator('#quickSummary')).to_contain_text('tablas')

    page.click('#quickExplore')
    expect(page.locator('#view-data')).to_be_visible()

    page.click('[data-view="dashboard"]')
    with page.expect_file_chooser() as chooser:
        page.click('#quickImport')
    chooser.value.set_files({
        'name': 'Datos_prueba.csv',
        'mimeType': 'text/csv',
        'buffer': 'Fecha,Linea,Produccion\\n2026-10-23,L1,120\\n'.replace('\\n', '\n').encode('utf-8')
    })
    expect(page.locator('#view-model')).to_be_visible()
    expect(page.locator('#tableTree')).to_contain_text('Datos_prueba')

    page.click('[data-view="dashboard"]')
    expect(page.locator('#quickSummary')).to_contain_text('Datos del proyecto cargados correctamente')
    page.click('#quickPrepare')
    expect(page.locator('#view-clean')).to_be_visible()
    assert not errors, errors


def test_quickstart_contrast_in_both_themes(browser_page):
    """The guided path remains legible in dark and light mode."""
    page, _, errors = browser_page
    def ratio(selector):
        return page.evaluate("""selector => {
          const fg = getComputedStyle(document.querySelector(selector)).color;
          const bg = getComputedStyle(document.querySelector('#quickstart')).backgroundColor;
          const luminance = value => {
            const rgb = value.match(/[0-9.]+/g).slice(0, 3).map(Number);
            const channels = rgb.map(x => {
              x /= 255;
              return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4;
            });
            return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
          };
          const a = luminance(fg), b = luminance(bg);
          return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
        }""", selector)

    for theme in ('dark', 'light'):
        if theme == 'light':
            page.click('#themeToggle')
            expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        assert ratio('#quickstart summary') >= 4.5, theme
        assert ratio('#quickExplore') >= 4.5, theme
        assert ratio('#quickPrepare') >= 4.5, theme
    assert not errors, errors
