"""Gráficos das previsões LOMO salvas. Não treina nem altera modelos."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
BASE = Path(__file__).resolve().parent

NOMES = {'KRR': 'Kernel Ridge', 'MLP': 'MLP', 'SVR': 'SVR', 'XGBoost': 'XGBoost'}
SERIES = [('y', 'Real', '#20252a', '-'), ('prevista', 'Previsão', '#1674bc', '-'),
          ('persistencia', 'Persistência', '#dd7b16', '--')]
NOTA = 'Teste LOMO • somente horários elegíveis • lacunas não representam geração zero'

def carregar():
    c = json.loads((BASE/'config.json').read_text())
    origem = BASE / 'resultados' / c['run_id'] / 'predicoes_lomo.csv'
    df = pd.read_csv(origem)
    df.index = pd.DatetimeIndex(pd.to_datetime(df.pop('timestamp'), utc=True)).tz_convert(c['timezone'])
    base = pd.read_csv(origem.parent/'auditoria_horaria.csv')
    base.index = pd.DatetimeIndex(pd.to_datetime(base.pop('timestamp'), utc=True)).tz_convert(c['timezone'])
    esperado = base.loc[base.M.eq(True)].sort_index()
    assert len(esperado) == 2750 and esperado.index.normalize().nunique() == 243
    assert esperado.index.min() >= pd.Timestamp('2024-08-01', tz=c['timezone'])
    assert esperado.index.max() < pd.Timestamp('2025-04-01', tz=c['timezone'])
    assert (esperado[['y', 'persistencia']] > 0).all().all()
    assert (pd.to_datetime(df.baseline_timestamp, utc=True) <= pd.to_datetime(df.emissao, utc=True)).all()
    assert set(df.modelo) == set(NOMES)
    for nome in NOMES:
        g = df.loc[df.modelo.eq(nome)].sort_index()
        assert g.index.is_unique and g.index.equals(esperado.index), nome
        for col in ['y', 'persistencia']:
            np.testing.assert_allclose(g[col], esperado[col])
        assert np.isfinite(g[['y', 'prevista', 'persistencia']]).all().all()
    return c, origem, df

def salvar(fig, arquivo):
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(arquivo, dpi=110, facecolor='white')

def quadro(titulo, ylabel):
    fig, ax = plt.subplots(figsize=(12, 4.4))
    fig.subplots_adjust(bottom=.22, top=.84, left=.08, right=.98)
    ax.set(title=titulo, ylabel=ylabel)
    ax.grid(alpha=.18)
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(.08, .035, NOTA, fontsize=9, color='#555555')
    return fig, ax

def panorama(g, nome, pasta, sufixo, diario=False):
    if diario:
        dados = g[['y', 'prevista', 'persistencia']].groupby(g.index.normalize()).sum()
        dados = dados.reindex(pd.date_range(g.index.min().normalize(), g.index.max().normalize(), freq='D'))
        rotulo = 'Soma nos horários avaliados (kWh)'
        titulo = f'{NOMES[nome]} | comparação diária no recorte avaliado'
    else:
        dados = g.reindex(pd.date_range(g.index.min().normalize(), g.index.max().normalize() + pd.Timedelta(hours=23), freq='h'))
        rotulo = 'Energia no intervalo de 1 h (kWh)'
        titulo = f'{NOMES[nome]} | comparação horária | {sufixo}'
    fig, ax = quadro(titulo, rotulo)
    for coluna, label, cor, estilo in SERIES:
        ax.plot(dados.index, dados[coluna], label=label, color=cor, ls=estilo, lw=1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y', tz=g.index.tz))
    ax.set_xlabel('Data local (UTC−3)')
    ax.legend(ncol=3, loc='upper left')
    if diario:
        fig.text(.08, .085, 'Não equivale à energia integral do dia: soma apenas dos mesmos horários usados nas métricas.', fontsize=9)
    salvar(fig, pasta / f'{nome}_{sufixo}.png')
    plt.close(fig)

def dias(g, nome, pasta, datas, ymax):
    fig, ax = quadro('', 'Energia no intervalo de 1 h (kWh)')
    linhas = [ax.plot([], [], color=cor, ls=estilo, marker='o', ms=3, lw=1.5, label=label)[0]
              for _, label, cor, estilo in SERIES]
    ax.set(xlim=(0, 23), ylim=(min(-.1, float(g.prevista.min())-.1), ymax), xlabel='Hora local (UTC−3)')
    ax.set_xticks(range(0, 24, 2))
    ax.legend(ncol=3, loc='upper left')
    for dia in datas:
        idx = pd.date_range(dia, periods=24, freq='h')
        d = g.reindex(idx)
        for linha, (coluna, _, _, _) in zip(linhas, SERIES):
            linha.set_data(range(24), d[coluna])
        valido = d.dropna(subset=['y', 'prevista', 'persistencia'])
        rmse = np.sqrt(np.mean((valido.prevista-valido.y)**2))
        rp = np.sqrt(np.mean((valido.persistencia-valido.y)**2))
        ax.set_title(f'{NOMES[nome]} | {dia:%d/%m/%Y}\n{len(valido)} horários • RMSE previsão: {rmse:.3f} kWh • persistência: {rp:.3f} kWh')
        salvar(fig, pasta / nome / f'{dia:%Y-%m-%d}.png')
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', choices=list(NOMES))
    parser.add_argument('--dia', help='AAAA-MM-DD, entre 2024-08-01 e 2025-03-31')
    parser.add_argument('--todos-dias', action='store_true')
    args = parser.parse_args()
    c, origem, df = carregar()
    out = BASE / 'graficos'
    datas = df.index.normalize().unique().sort_values()
    if args.dia:
        escolhido = pd.Timestamp(args.dia).tz_localize(c['timezone'])
        if escolhido not in datas:
            parser.error('Dia fora do período avaliado.')
        selecionadas = [escolhido]
    else:
        selecionadas = datas if args.todos_dias else datas[:1]
    ymax = float(df[['y', 'prevista', 'persistencia']].max().max()) * 1.18
    for nome in ([args.modelo] if args.modelo else NOMES):
        g = df.loc[df.modelo.eq(nome)].sort_index()
        if not args.dia:
            panorama(g, nome, out/'horarios', 'periodo_completo')
            panorama(g, nome, out/'resumos_diarios', 'comparacao_diaria', diario=True)
            for mes, grupo in g.groupby(g.index.strftime('%Y-%m')):
                panorama(grupo, nome, out/'horarios', mes)
        dias(g, nome, out/'dias', selecionadas, ymax)
        print(f'{nome}: {len(selecionadas)} gráficos diários concluídos.', flush=True)
    if args.todos_dias and not args.modelo and not args.dia:
        auditoria = {'fonte': str(origem.relative_to(BASE)), 'sha256': hashlib.sha256(origem.read_bytes()).hexdigest(),
                     'matplotlib': matplotlib.__version__, 'modelos': list(NOMES), 'dias': len(datas),
                     'amostras_por_modelo': len(df)//len(NOMES), 'pngs': len(list(out.rglob('*.png'))),
                     'interpretacao': NOTA, 'somas': 'Somente horários elegíveis, não energia integral do dia.'}
        (out/'auditoria_graficos.json').write_text(json.dumps(auditoria, indent=2, ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__':
    main()
