import csv, gzip, json, re, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW, MANUAL, CSV_DIR = BASE / 'raw', BASE / 'manual', BASE / 'csv'
SQL_OUT = BASE.parent / '03_carga_datos.sql'
ANIOS = ['2024', '2025', '2026']
ESPORTS = ['Counter-Strike 2', 'League of Legends', 'Rocket League']
UA = 'UdeSA-BD-TP/1.0 (trabajo practico universitario; uso unico con cache local)'
MESES = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}

def fetch(wiki, titles, cache):
    path = RAW / f'{cache}.json'
    if not path.exists():
        pages, redirects = {}, {}
        for i in range(0, len(titles), 50):
            q = urllib.parse.urlencode({
                'action': 'query', 'prop': 'revisions', 'rvprop': 'content',
                'rvslots': 'main', 'format': 'json', 'redirects': 1,
                'titles': '|'.join(titles[i:i + 50])})
            req = urllib.request.Request(f'https://liquipedia.net/{wiki}/api.php?{q}',
                                         headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req) as r:
                body = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    body = gzip.decompress(body)
            d = json.loads(body)['query']
            for k in ('normalized', 'redirects'):
                for x in d.get(k, []):
                    redirects[x['from']] = x['to']
            for p in d['pages'].values():
                if 'revisions' in p:
                    pages[p['title']] = p['revisions'][0]['slots']['main']['*']
            time.sleep(2.5)  # límite de la API: 1 pedido cada 2 s
        path.write_text(json.dumps({'pages': pages, 'redirects': redirects}, ensure_ascii=False), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def resolve(data, title):
    for t in (title, title[:1].upper() + title[1:]):
        seen = set()
        while t in data['redirects'] and t not in seen:
            seen.add(t)
            t = data['redirects'][t]
        if t in data['pages']:
            return t
    return None


def page(data, title):
    t = resolve(data, title)
    return data['pages'][t] if t else None


def main_pages():
    out = {}
    for name in ('ediciones', 'standings'):
        d = json.loads((RAW / f'{name}.json').read_text(encoding='utf-8'))
        for p in d['query']['pages'].values():
            out[p['title']] = p['revisions'][0]['slots']['main']['*']
    return out

def cierre(t, i):
    depth = 0
    while i < len(t):
        if t.startswith('{{', i):
            depth += 1; i += 2
        elif t.startswith('}}', i):
            depth -= 1; i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return i


def params(tpl):
    body, out, depth, cur = tpl[2:-2], [], 0, ''
    for i, ch in enumerate(body):
        if body.startswith('{{', i) or body.startswith('[[', i):
            depth += 1
        elif (body.startswith('}}', i) or body.startswith(']]', i)) and depth:
            depth -= 1
        if ch == '|' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return {k.strip(): v.strip() for k, v in (p.split('=', 1) for p in out[1:] if '=' in p)}


def texto(x):
    x = re.sub(r'<!--.*?-->|<ref.*?(</ref>|/>)', '', x, flags=re.S)
    x = re.sub(r'\{\{[^{}]*\}\}', '', x)
    x = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', x)
    x = re.sub(r"<[^>]+>|'''?", '', x)
    return re.sub(r'\s+', ' ', x).strip()


def numero(x):
    x = re.sub(r'<!--.*', '', x or '')
    x = re.sub(r'[^\d.]', '', x)
    if not x:
        return None
    return x[:-3] if x.endswith('.00') else x


def fecha(x):
    m = re.match(r'(\d{4})(?:-(\d{2}|\?\?))?(?:-(\d{2}|\?\?))?', (x or '').strip())
    if not m:
        return None
    a, mes, dia = m[1], m[2], m[3]
    mes = mes if mes and mes != '??' else '01'
    dia = dia if dia and dia != '??' else '01'
    return f'{a}-{mes}-{dia}'


def rango_fechas(x, anio):
    m = re.search(r'([A-Z][a-z]{2}) (\d+) - (?:([A-Z][a-z]{2}) )?(\d+), (\d{4})', x)
    m1, d1, m2, d2, a = m[1], m[2], m[3] or m[1], m[4], m[5]
    f = lambda mes, d: f'{a}-{MESES[mes.lower()]:02d}-{int(d):02d}'
    return f(m1, d1), f(m2, d2)


def leer_csv(nombre):
    with open(MANUAL / nombre, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def standings(anio, pages):
    t = pages[f'Esports World Cup/{anio}/Club Championship Standings']
    torneos = []
    for i, link in re.findall(r'\|tournament(\d+)=([^\n|]+)', t):
        wiki, pag = link.strip().split(':', 1)
        nombre = re.search(r'\|tournament' + i + r'name=.*\[\[[^|\]]*\|([^\]]*)\]\]', t)[1]
        torneos.append((int(i), wiki, pag.replace('_', ' ').strip(), nombre))
    orgs = []
    for m in re.finditer(r'\|team\d+=\{\{RankingsTableRow\|([^|\n]+)(.*?)\n\}\}', t, re.S):
        pts = {int(k): int(v) for k, v in re.findall(r'\|points(\d+)=(\d+)', m[2])}
        orgs.append((m[1].strip().replace('_', ' '), pts))
    return torneos, orgs


def tabla_torneos(t):
    s = t.find('===EWC Main Tournaments===')
    e = t.find('\n|}', s)
    filas = []
    for r in t[s:e].split('\n|-')[1:]:
        celdas = [c.strip() for c in re.split(r'\n\|\s?', '\n' + r.strip()) if c.strip()]
        if len(celdas) >= 5 and not celdas[0].startswith('!'):
            filas.append(celdas)
    return filas


def premios(t):
    bloques = []
    for m in re.finditer(r'\{\{(?!Award)(\w*)PrizePool\b', t):
        tpl = t[m.start():cierre(t, m.start())]
        header = tpl[:tpl.find('{{Slot')] if '{{Slot' in tpl else tpl
        clave = re.search(r'\|\s*(points\d?)\s*=\s*ewc', header)
        slots = []
        for s in re.finditer(r'\{\{Slot\b', tpl):
            slot = tpl[s.start():cierre(tpl, s.start())]
            p = params(slot)
            if 'award' in p:
                continue
            opp = slot.find('{{Opponent', 2)
            if opp >= 0 and 'usdprize' not in p:
                p = {**params(slot[opp:cierre(slot, opp)]), **{k: v for k, v in p.items() if not k.startswith('{{')}}
            slots.append(p)
        bloques.append((clave[1] if clave else None, slots))
    elegido = next((b for b in bloques if b[0]), None)
    if not elegido:
        elegido = next((('points', s) for _, s in bloques if s and numero(s[0].get('points')) == '1000'), None)
    if not elegido:
        return []
    clave, slots = elegido
    out, pos = [], 1
    for p in slots:
        if p.get('place'):
            a, _, b = p['place'].partition('-')
            inicio, tam = int(a), int(b or a) - int(a) + 1
        else:
            inicio, tam = pos, int(numero(p.get('count')) or 1)
        pos = inicio + tam
        valor = p.get(clave) if clave in p else p.get({'points1': 'points', 'points': 'points1'}.get(clave, ''))
        premio, puntos = numero(p.get('usdprize')), numero(valor)
        if premio or puntos:
            out.append((inicio, int(puntos or 0), premio or '0'))
    return out


def formato(t):
    m = re.search(r'==+\s*Format\s*==+(.*?)\n==(?!=)', t, re.S) or re.search(r'==+\s*Format\s*==+(.*)', t, re.S)
    if not m:
        return None
    etapas = []
    for linea in m[1].split('\n'):
        negrita = re.search(r"'''(.*?)'''", linea)
        if re.match(r'\*\s*[^*]', linea) and negrita:
            nombre = re.split(r' [-–(]|:', texto(negrita[1]))[0].strip()
            if nombre and nombre not in etapas and not re.match(r'(?i)(bo\d|\d|participants|patch|schedule|notes?\b)', nombre):
                etapas.append(nombre)
    return ' + '.join(etapas)[:80] or None


PAISES = {
    'Argentina': 'Argentina', 'Armenia': 'Armenia', 'Australia': 'Australia', 'Brazil': 'Brasil',
    'Cambodia': 'Camboya', 'Canada': 'Canadá', 'China': 'China', 'Finland': 'Finlandia', 'France': 'Francia',
    'Germany': 'Alemania', 'Hong Kong': 'Hong Kong', 'India': 'India', 'Indonesia': 'Indonesia',
    'Italy': 'Italia', 'Japan': 'Japón', 'Kazakhstan': 'Kazajistán', 'Korea': 'Corea del Sur',
    'South Korea': 'Corea del Sur', 'Malaysia': 'Malasia', 'my': 'Malasia', 'Mongolia': 'Mongolia',
    'Myanmar': 'Myanmar', 'Nepal': 'Nepal', 'Netherlands': 'Países Bajos', 'Norway': 'Noruega',
    'Pakistan': 'Pakistán', 'Philippines': 'Filipinas', 'Portugal': 'Portugal', 'Qatar': 'Catar',
    'Romania': 'Rumania', 'Russia': 'Rusia', 'Saudi Arabia': 'Arabia Saudita', 'Serbia': 'Serbia',
    'Singapore': 'Singapur', 'Spain': 'España', 'Sweden': 'Suecia', 'Switzerland': 'Suiza',
    'Taiwan': 'Taiwán', 'Thailand': 'Tailandia', 'Turkey': 'Turquía', 'turkey': 'Turquía',
    'US': 'Estados Unidos', 'United States': 'Estados Unidos', 'USA': 'Estados Unidos',
    'Ukraine': 'Ucrania', 'United Arab Emirates': 'Emiratos Árabes Unidos', 'United Kingdom': 'Reino Unido',
    'UK': 'Reino Unido', 'Vietnam': 'Vietnam', 'Denmark': 'Dinamarca', 'Poland': 'Polonia',
    'Belgium': 'Bélgica', 'Mexico': 'México', 'Chile': 'Chile', 'Peru': 'Perú', 'Egypt': 'Egipto',
    'Kuwait': 'Kuwait', 'Bahrain': 'Baréin', 'Jordan': 'Jordania', 'Morocco': 'Marruecos',
    'br': 'Brasil', 'korea': 'Corea del Sur',
    'Europe': None, 'South America': None,
}

def fechas_created(txt):
    """'{{Org}}: 2016-04-18<br>{{apex}}: 2019-02-25' → ('2016-04-18', '2019-02-25')."""
    org = juego = None
    for tpl, f in re.findall(r'\{\{(\w+)\}\}\s*:\s*([\d?-]+)', txt or ''):
        if tpl.lower() == 'org':
            org = org or fecha(f)
        else:
            juego = juego or fecha(f)
    if not org and not juego:
        juego = fecha(txt)
    return org, juego

def infobox(t):
    ib = re.search(r'\{\{Infobox team(.*?)\n\}\}', t or '', re.S)
    body = ib[1] if ib else ''
    get = lambda k: (re.search(r'\|' + k + r'\s*=\s*([^|\n]*)', body) or [0, ''])[1].strip()
    return texto(get('location')), get('created')

def construir():
    pages = main_pages()
    alias_esp = leer_csv('alias_esports.csv')
    alias_org = {r['variante'].lower(): r for r in leer_csv('alias_orgs.csv')}
    excepciones = {(int(r['anio_edicion']), r['nombre_esport'], r['org'].lower()) for r in leer_csv('excepciones.csv')}
    paises_manual = {r['nombre_org']: r['pais'] for r in leer_csv('paises_orgs.csv')}
    errores = []

    def esport_de(wiki, texto_):
        for r in alias_esp:
            if r['wiki'] == wiki and r['contiene'] in texto_:
                return r['nombre_esport']
        raise ValueError(f'esport sin alias: {wiki} {texto_}')

    T = defaultdict(list)
    esports = {r['nombre_esport']: r for r in leer_csv('esports.csv')}

    torneos = {}
    for anio in ANIOS:
        t = pages[f'Esports World Cup/{anio}']
        g = lambda k: re.search(r'\|' + k + r'=([^|\n]*)', t)[1].strip()
        T['ediciones'].append([int(anio), {'Riyadh': 'Riad', 'Paris': 'París'}.get(g('city'), g('city')),
                               g('sdate'), g('edate'), numero(g('prizepoolusd'))])
        for c in tabla_torneos(t):
            wiki, pag = re.search(r'\[\[(\w+):([^|\]]+)', c[2]).groups()
            esp = esport_de(wiki, pag.replace('_', ' ') + ' ' + c[2])
            ini, fin = rango_fechas(c[1], anio)
            part = re.search(r'(\d+) Teams', c[4]) or re.search(r'(\d+)', c[4])
            torneos[(int(anio), esp)] = [int(anio), esp, ini, fin, numero(texto(c[3])), None, int(part[1])]

    datos_wiki = {}
    wiki_data = lambda w, pre: datos_wiki.setdefault((pre, w), fetch(w, [], f'{pre}_{w}'))
    puntos_de = {}
    participa = []
    for anio in ANIOS:
        lista, filas = standings(anio, pages)
        info = {}
        for i, wiki, pag, nombre in lista:
            esp = esport_de(wiki, pag + ' ' + nombre)
            if esp not in esports:
                errores.append(f'esport sin datos en esports.csv: {esp}')
            key = (int(anio), esp)
            if key not in torneos:
                errores.append(f'torneo de standings sin fila en la tabla de la edición: {key}')
                continue
            t = page(wiki_data(wiki, 'torneos'), pag)
            torneos[key][5] = formato(t)
            slots = premios(t)
            if not slots:
                errores.append(f'sin tabla de premios: {key}')
            for pos, pts, premio in slots:
                T['tabla_puntos'].append([key[0], esp, pos, pts, premio])
            por_puntos = defaultdict(list)
            for pos, pts, _ in slots:
                if pts > 0:
                    por_puntos[pts].append(pos)
            puntos_de[key] = por_puntos
            info[i] = (wiki, esp)
        for org, pts in filas:
            for i, v in pts.items():
                if v > 0 and i in info:
                    wiki, esp = info[i]
                    if (int(anio), esp, org.lower()) in excepciones:
                        continue
                    pos = puntos_de[(int(anio), esp)].get(v)
                    if not pos or len(pos) > 1:
                        errores.append(f'{anio} {esp} {org}: {v} puntos no corresponden a un único puesto ({pos})')
                        continue
                    participa.append((org, wiki, esp, int(anio), pos[0]))

    esp_wiki = fetch('esports', [], 'organizaciones')
    canon, pais, fundacion, creado = {}, defaultdict(Counter), {}, {}
    sin_traducir = set()
    for org, wiki, esp, anio, pos in participa:
        a = alias_org.get(org.lower())
        if org not in canon:
            nombre = a['nombre_org'] if a else (resolve(esp_wiki, org) or resolve(wiki_data(wiki, 'equipos'), org) or org)
            a2 = alias_org.get(nombre.lower())
            canon[org] = a2['nombre_org'] if a2 else nombre
        nombre = canon[org]
        titulo = (a['pagina'] or a['nombre_org']) if a else org
        pag_org = page(esp_wiki, titulo) or page(esp_wiki, org)
        pag_equipo = (page(wiki_data(wiki, 'equipos'), titulo) or page(wiki_data(wiki, 'equipos'), org)
                      or page(wiki_data(wiki, 'equipos2'), titulo))
        for t, es_equipo in ((pag_org, False), (pag_equipo, True)):
            loc, created = infobox(t)
            f_org, f_juego = fechas_created(created)
            if loc:
                if loc not in PAISES:
                    sin_traducir.add(loc)
                elif PAISES[loc]:
                    pais[nombre][PAISES[loc]] += 1
            if f_org:
                fundacion.setdefault(nombre, f_org)
            if es_equipo and f_juego:
                creado.setdefault((nombre, esp), f_juego)
    if sin_traducir:
        errores.append(f'países sin traducir en PAISES: {sorted(sin_traducir)}')
        
    por_minus = defaultdict(set)
    for n in canon.values():
        por_minus[n.lower()].add(n)
    unico = {n: sorted(v, key=lambda s: (s.islower(), s))[0] for v in por_minus.values() for n in v}

    vistos = set()
    for org, wiki, esp, anio, pos in participa:
        nombre = unico[canon[org]]
        if (nombre, esp, anio) in vistos:
            errores.append(f'participación repetida: {nombre} {esp} {anio}')
            continue
        vistos.add((nombre, esp, anio))
        T['participaciones'].append([nombre, esp, anio, pos])
    orgs = sorted({r[0] for r in T['participaciones']})
    for n in orgs:
        variantes = [v for v in por_minus[n.lower()]]
        c = sum((pais[v] for v in variantes), Counter())
        f = next((fundacion[v] for v in variantes if v in fundacion), None)
        p = paises_manual.get(n) or (c.most_common(1)[0][0] if c else 'Sin datos')
        T['organizaciones'].append([n, p, f])
    equipos = sorted({(r[0], r[1]) for r in T['participaciones']})
    for n, esp in equipos:
        f = next((creado[(v, esp)] for v in por_minus[n.lower()] if (v, esp) in creado), None)
        T['equipos'].append([n, esp, f])

    usados = sorted({k[1] for k in torneos})
    for e in usados:
        r = esports[e]
        T['esports'].append([e, r['genero'], r['desarrolladora'], int(r['jugadores_por_equipo'])])
    T['torneos'] = [torneos[k] for k in sorted(torneos)]

    for r in leer_csv('sponsors.csv'):
        T['sponsors'].append([r['nombre_sponsor'], r['rubro'], r['pais']])
    for r in leer_csv('sponsors_edicion.csv'):
        T['sponsors_edicion'].append([r['nombre_sponsor'], r['monto_anual'], int(r['duracion_contrato']), r['categoria']])
    for r in leer_csv('sponsors_equipo.csv'):
        T['sponsors_equipo'].append([r['nombre_sponsor'], r['monto_anual'], int(r['duracion_contrato']), r['espacio_camiseta']])
    for r in leer_csv('patrocinios_edicion.csv'):
        T['patrocinios_edicion'].append([r['nombre_sponsor'], int(r['anio_edicion'])])
    eq = set(equipos)
    for r in leer_csv('patrocinios_equipo.csv'):
        if (r['nombre_org'], r['nombre_esport']) not in eq:
            errores.append(f"patrocinio a un equipo que no está en equipos: {r['nombre_org']} / {r['nombre_esport']}")
        T['patrocinios_equipo'].append([r['nombre_sponsor'], r['nombre_org'], r['nombre_esport']])
    return T, errores



COLUMNAS = {
    'organizaciones': ['nombre_org', 'pais', 'fecha_fundacion'],
    'ediciones': ['anio_edicion', 'ciudad', 'fecha_inicio', 'fecha_fin', 'pozo_total'],
    'esports': ['nombre_esport', 'genero', 'desarrolladora', 'jugadores_por_equipo'],
    'sponsors': ['nombre_sponsor', 'rubro', 'pais'],
    'equipos': ['nombre_org', 'nombre_esport', 'fecha_creacion'],
    'torneos': ['anio_edicion', 'nombre_esport', 'fecha_inicio', 'fecha_fin', 'pozo', 'formato', 'cantidad_equipos'],
    'sponsors_edicion': ['nombre_sponsor', 'monto_anual', 'duracion_contrato', 'categoria'],
    'sponsors_equipo': ['nombre_sponsor', 'monto_anual', 'duracion_contrato', 'espacio_camiseta'],
    'tabla_puntos': ['anio_edicion', 'nombre_esport', 'posicion_final', 'puntos', 'premio'],
    'patrocinios_edicion': ['nombre_sponsor', 'anio_edicion'],
    'patrocinios_equipo': ['nombre_sponsor', 'nombre_org', 'nombre_esport'],
    'participaciones': ['nombre_org', 'nombre_esport', 'anio_edicion', 'posicion_final'],
}
NUMERICAS = {'anio_edicion', 'pozo_total', 'jugadores_por_equipo', 'pozo', 'cantidad_equipos',
             'monto_anual', 'duracion_contrato', 'posicion_final', 'puntos', 'premio'}

def sql_valor(col, v):
    if v is None:
        return 'NULL'
    if col in NUMERICAS:
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

def recortar(T):
    """Deja solo los esports de ESPORTS, arrastrando en cascada lo que depende de ellos.

    El recorte es de los datos, no del diseño: el modelo admite cualquier cantidad
    de esports. Hay que arrastrar la cascada porque, si no, quedan organizaciones
    sin ningun equipo y sponsors sin ningun patrocinio, y eso viola las
    participaciones totales del diagrama."""
    if not ESPORTS:
        return T
    keep = set(ESPORTS)
    col = {t: COLUMNAS[t].index('nombre_esport') for t in
           ('esports', 'equipos', 'torneos', 'tabla_puntos', 'patrocinios_equipo', 'participaciones')}
    for t, i in col.items():
        T[t] = [f for f in T[t] if f[i] in keep]

    # organizaciones que se quedaron sin equipos
    orgs = {f[COLUMNAS['equipos'].index('nombre_org')] for f in T['equipos']}
    T['organizaciones'] = [f for f in T['organizaciones'] if f[0] in orgs]

    # sponsors de equipo que se quedaron sin patrocinios
    con_patro = {f[0] for f in T['patrocinios_equipo']}
    T['sponsors_equipo'] = [f for f in T['sponsors_equipo'] if f[0] in con_patro]

    # sponsors que quedaron fuera de los dos subtipos
    subtipos = {f[0] for f in T['sponsors_equipo']} | {f[0] for f in T['sponsors_edicion']}
    T['sponsors'] = [f for f in T['sponsors'] if f[0] in subtipos]
    return T


def escribir(T):
    CSV_DIR.mkdir(exist_ok=True)
    for tabla, cols in COLUMNAS.items():
        with open(CSV_DIR / f'{tabla}.csv', 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(T[tabla])
    orden = list(COLUMNAS)
    out = ['BEGIN;', '', 'TRUNCATE ' + ', '.join(reversed(orden)) + ';']
    for tabla in orden:
        cols = COLUMNAS[tabla]
        filas = T[tabla]
        for i in range(0, len(filas), 200):
            valores = ',\n'.join('  (' + ', '.join(sql_valor(c, v) for c, v in zip(cols, fila)) + ')'
                                 for fila in filas[i:i + 200])
            out.append(f'\nINSERT INTO {tabla} ({", ".join(cols)}) VALUES\n{valores};')
    out += ['', 'COMMIT;', '']
    SQL_OUT.write_text('\n'.join(out), encoding='utf-8')


def descargar_todo():
    pages = main_pages()
    por_wiki, orgs, equipos = {}, set(), {}
    for anio in ANIOS:
        torneos, filas = standings(anio, pages)
        wiki_de = {i: wiki for i, wiki, _, _ in torneos}
        for _, wiki, pag, _ in torneos:
            por_wiki.setdefault(wiki, []).append(pag)
        for org, pts in filas:
            for i, v in pts.items():
                if v > 0:
                    orgs.add(org)
                    equipos.setdefault(wiki_de[i], set()).add(org)
    for wiki, titles in sorted(por_wiki.items()):
        fetch(wiki, sorted(set(titles)), f'torneos_{wiki}')
    fetch('esports', sorted(orgs), 'organizaciones')
    # página del equipo de cada org en la wiki de cada juego: país y fecha de creación
    for wiki, nombres in sorted(equipos.items()):
        fetch(wiki, sorted(nombres), f'equipos_{wiki}')
    # páginas con otro título, definidas en manual/alias_orgs.csv
    alias = {r['variante'].lower(): r for r in leer_csv('alias_orgs.csv')}
    for wiki, nombres in sorted(equipos.items()):
        extra = sorted({alias[n.lower()]['pagina'] for n in nombres if n.lower() in alias and alias[n.lower()]['pagina']})
        fetch(wiki, extra, f'equipos2_{wiki}')


if __name__ == '__main__':
    descargar_todo()
    T, errores = construir()
    T = recortar(T)
    for tabla in COLUMNAS:
        print(f'{tabla:20} {len(T[tabla]):5} filas')
    if errores:
        print(f'\n{len(errores)} problemas:')
        print('\n'.join('  - ' + e for e in errores))
        sys.exit(1)
    escribir(T)
    print(f'\nOK: {SQL_OUT.name} y datos/csv/ generados.')
