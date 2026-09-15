"""Acrescenta células de visualização ao notebook sem apagar saídas existentes."""
import nbformat as nb
from pathlib import Path

BASE = Path(__file__).resolve().parent

def integrar():
    path = BASE/'Pipeline_SGIE_ROBUSTO_V2.ipynb'
    notebook = nb.read(path, as_version=4)
    notebook.cells = [cell for cell in notebook.cells if 'sgie_graficos' not in cell.metadata.get('tags', [])]
    cells = [nb.v4.new_markdown_cell('## Gráficos por modelo e por dia\n\nPrevisões de teste LOMO, não previsões dos modelos finais sobre o próprio treino. Os horários excluídos ficam como lacunas. As somas diárias abrangem somente os horários elegíveis. LOMO e meteorologia histórica não comprovam desempenho operacional day-ahead.'),
             nb.v4.new_code_cell("from pathlib import Path\nimport subprocess, sys\nfrom IPython.display import Image, display\nBASE = Path.cwd()\nassert (BASE/'plotar_resultados.py').exists(), 'Abra o notebook na pasta do pipeline.'\nif not (BASE/'graficos/auditoria_graficos.json').exists():\n    subprocess.run([sys.executable, str(BASE/'plotar_resultados.py'), '--todos-dias'], check=True)\nprint('Gráficos disponíveis para KRR, MLP, SVR e XGBoost.')"),
             nb.v4.new_code_cell("for modelo in ['KRR', 'MLP', 'SVR', 'XGBoost']:\n    display(Image(filename=str(BASE/'graficos/horarios'/f'{modelo}_periodo_completo.png')))"),
             nb.v4.new_code_cell("for modelo in ['KRR', 'MLP', 'SVR', 'XGBoost']:\n    display(Image(filename=str(BASE/'graficos/resumos_diarios'/f'{modelo}_comparacao_diaria.png')))"),
             nb.v4.new_code_cell("# Altere o dia para qualquer data entre 01/08/2024 e 31/03/2025.\nDIA = '2024-08-01'\nfor MODELO in ['KRR', 'MLP', 'SVR', 'XGBoost']:\n    display(Image(filename=str(BASE/'graficos/dias'/MODELO/f'{DIA}.png')))" )]
    for cell in cells:
        cell.metadata['tags'] = ['sgie_graficos']
    notebook.cells.extend(cells)
    nb.write(notebook, path)

if __name__ == '__main__':
    integrar()
