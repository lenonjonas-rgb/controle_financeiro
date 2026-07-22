import flet as ft
import sqlite3
from datetime import datetime, timedelta
import os
import flet_fastapi

# ==========================================
# 1. BANCO DE DADOS
# ==========================================
def inicializar_banco():
    conexao = sqlite3.connect("banco_financeiro.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            valor REAL,
            empresa TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas_cadastradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    conexao.commit()
    conexao.close()

def salvar_no_banco(data, tipo, categoria, valor, empresa):
    conexao = sqlite3.connect("banco_financeiro.db")
    cursor = conexao.cursor()
    
    if isinstance(valor, str):
        valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_float = float(valor_limpo) if valor_limpo else 0.0
    else:
        valor_float = float(valor)

    cursor.execute("""
        INSERT INTO lancamentos (data, tipo, categoria, valor, empresa)
        VALUES (?, ?, ?, ?, ?)
    """, (data, tipo, categoria, valor_float, empresa))
    
    cursor.execute("""
        INSERT OR IGNORE INTO empresas_cadastradas (nome) VALUES (?)
    """, (empresa.strip(),))

    conexao.commit()
    conexao.close()

def deletar_lancamento(id_registro):
    conexao = sqlite3.connect("banco_financeiro.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM lancamentos WHERE id = ?", (id_registro,))
    conexao.commit()
    conexao.close()

def buscar_empresas_salvas():
    conexao = sqlite3.connect("banco_financeiro.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT nome FROM empresas_cadastradas ORDER BY nome ASC")
    linhas = cursor.fetchall()
    conexao.close()
    return [r[0] for r in linhas]

# ==========================================
# 2. APLICAÇÃO VISUAL FLET WEB
# ==========================================
def main(page: ft.Page):
    try:
        page.title = "Controle Financeiro Web"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 10
        page.scroll = ft.ScrollMode.AUTO
        
        inicializar_banco()
        data_hoje = datetime.now().strftime("%d/%m/%Y")

        input_data = ft.TextField(
            label="1. Data da Transação", 
            value=data_hoje, 
            hint_text="DD/MM/AAAA",
            expand=True
        )

        def set_data_hoje(e):
            input_data.value = datetime.now().strftime("%d/%m/%Y")
            input_data.update()

        def set_data_ontem(e):
            ontem = datetime.now() - timedelta(days=1)
            input_data.value = ontem.strftime("%d/%m/%Y")
            input_data.update()

        input_tipo = ft.Dropdown(
            label="2. Tipo de Movimentação",
            options=[
                ft.dropdown.Option("saida", text="Saída (-)"),
                ft.dropdown.Option("entrada", text="Entrada (+)"),
            ],
            value="saida",
            expand=True
        )

        input_categoria = ft.Dropdown(
            label="3. Categoria",
            options=[
                ft.dropdown.Option("Alimentação"),
                ft.dropdown.Option("Transporte / Veículos"),
                ft.dropdown.Option("Manutenção / Ferramentas"),
                ft.dropdown.Option("Lazer / Pessoal"),
                ft.dropdown.Option("Saúde"),
                ft.dropdown.Option("Moradia / Aluguel"),
                ft.dropdown.Option("Fornecedores / Materiais"),
                ft.dropdown.Option("Receita / Salário / Vendas"),
                ft.dropdown.Option("Outros"),
            ],
            expand=True
        )

        input_valor = ft.TextField(
            label="4. Valor (R$)", 
            hint_text="Ex: 150,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True
        )

        input_empresa = ft.TextField(
            label="5. Empresa / Favorecido", 
            hint_text="Digite o nome...",
            expand=True
        )

        def carregar_opcoes_empresas():
            empresas = buscar_empresas_salvas()
            return [ft.dropdown.Option(emp) for emp in empresas]

        def selecionar_empresa_historico(e):
            if e.control.value:
                input_empresa.value = e.control.value
                input_empresa.update()

        dropdown_empresas = ft.Dropdown(
            label="Histórico de Empresas",
            options=carregar_opcoes_empresas(),
            on_change=selecionar_empresa_historico,
            hint_text="Selecionar salva...",
            expand=True
        )

        def mostrar_snack(mensagem):
            page.snack_bar = ft.SnackBar(ft.Text(mensagem))
            page.snack_bar.open = True
            page.update()

        def executar_salvamento(e):
            try:
                empresa_valor = input_empresa.value.strip() if input_empresa.value else ""

                if not input_data.value:
                    mostrar_snack("Por favor, informe a data!")
                    return
                if not input_categoria.value:
                    mostrar_snack("Selecione uma categoria!")
                    return
                if not input_valor.value:
                    mostrar_snack("Informe o valor da transação!")
                    return
                if not empresa_valor:
                    mostrar_snack("Digite o nome da empresa ou favorecido!")
                    return

                data_final = input_data.value.strip()
                if len(data_final) == 5 and "/" in data_final:
                    ano_atual = datetime.now().year
                    data_final = f"{data_final}/{ano_atual}"

                salvar_no_banco(
                    data=data_final,
                    tipo=input_tipo.value,
                    categoria=input_categoria.value,
                    valor=input_valor.value,
                    empresa=empresa_valor
                )

                mostrar_snack("Lançamento salvo com sucesso!")

                input_valor.value = ""
                input_empresa.value = ""
                input_categoria.value = None
                dropdown_empresas.value = None
                dropdown_empresas.options = carregar_opcoes_empresas()
                
                mudar_tela_interface(1)

            except Exception as erro:
                mostrar_snack(f"Erro ao salvar: {str(erro)}")

        def mudar_tela_interface(indice_aba):
            barra_lateral.selected_index = indice_aba
            barra_lateral.update()

            conteudo_central.controls.clear()
            if indice_aba == 0:
                conteudo_central.controls.append(criar_tela_formulario())
            elif indice_aba == 1:
                conteudo_central.controls.append(criar_tela_relatorio())
            page.update()

        barra_lateral = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=70,
            destinations=[
                ft.NavigationRailDestination(icon=ft.icons.ADD_CARD, label="Novo"),
                ft.NavigationRailDestination(icon=ft.icons.ANALYTICS, label="Relatórios"),
            ],
            on_change=lambda e: mudar_tela_interface(e.control.selected_index),
        )

        conteudo_central = ft.Column(expand=True, alignment=ft.MainAxisAlignment.START)

        def criar_tela_formulario():
            return ft.Container(
                content=ft.Column([
                    ft.Text("Novo Lançamento Financeiro", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Preencha os dados da transação abaixo.", size=12, color=ft.colors.GREY_400),
                    ft.Divider(),
                    
                    ft.ResponsiveRow([
                        ft.Column([input_data], col={"xs": 12, "sm": 7}),
                        ft.Column([
                            ft.Row([
                                ft.OutlinedButton("Hoje", on_click=set_data_hoje),
                                ft.OutlinedButton("Ontem", on_click=set_data_ontem),
                            ], alignment=ft.MainAxisAlignment.START)
                        ], col={"xs": 12, "sm": 5}),
                    ]),
                    
                    ft.ResponsiveRow([
                        ft.Column([input_tipo], col={"xs": 12, "sm": 6}),
                        ft.Column([input_categoria], col={"xs": 12, "sm": 6}),
                    ]),

                    ft.ResponsiveRow([
                        ft.Column([input_valor], col={"xs": 12, "sm": 6}),
                    ]),
                    
                    ft.ResponsiveRow([
                        ft.Column([input_empresa], col={"xs": 12, "sm": 7}),
                        ft.Column([dropdown_empresas], col={"xs": 12, "sm": 5}),
                    ]),
                    
                    ft.Container(height=10),
                    
                    ft.ResponsiveRow([
                        ft.Column([
                            ft.ElevatedButton(
                                "Salvar Lançamento", 
                                icon=ft.icons.SAVE, 
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.GREEN_700,
                                    color=ft.colors.WHITE,
                                    padding=15
                                ),
                                on_click=executar_salvamento,
                                width=1000
                            )
                        ], col={"xs": 12})
                    ])
                ], spacing=12),
                padding=10
            )

        def criar_tela_relatorio():
            data_referencia = [datetime.now()]
            meses_extenso = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            texto_mes_ano = ft.Text(
                f"{meses_extenso[data_referencia[0].month - 1]} / {data_referencia[0].year}", 
                size=16, 
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_200
            )

            container_dashboard = ft.Column(spacing=15)

            def atualizar_relatorio_mensal():
                mes_ano = data_referencia[0].strftime("%m/%Y")
                texto_mes_ano.value = f"{meses_extenso[data_referencia[0].month - 1]} / {data_referencia[0].year}"
                
                conexao = sqlite3.connect("banco_financeiro.db")
                cursor = conexao.cursor()
                cursor.execute("""
                    SELECT tipo, categoria, valor, empresa, data 
                    FROM lancamentos 
                    WHERE data LIKE ? 
                    ORDER BY id DESC
                """, (f"%/{mes_ano}",))
                registros = cursor.fetchall()
                conexao.close()

                total_entradas = sum(v for t, c, v, emp, dt in registros if t == 'entrada')
                total_saidas = sum(v for t, c, v, emp, dt in registros if t == 'saida')
                saldo = total_entradas - total_saidas

                gastos_por_categoria = {}
                for t, cat, val, emp, dt in registros:
                    if t == 'saida':
                        gastos_por_categoria[cat] = gastos_por_categoria.get(cat, 0.0) + val

                linhas_categoria = []
                for cat, valor_total in gastos_por_categoria.items():
                    porcentagem = (valor_total / total_saidas * 100) if total_saidas > 0 else 0
                    linhas_categoria.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(cat, weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(f"R$ {valor_total:.2f}")),
                            ft.DataCell(ft.Text(f"{porcentagem:.1f}%")),
                        ])
                    )

                tabela_categorias = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Categoria")),
                        ft.DataColumn(ft.Text("Total")),
                        ft.DataColumn(ft.Text("%")),
                    ],
                    rows=linhas_categoria
                )

                card_entradas = ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Text("Entradas", size=11, color=ft.colors.GREY_400), 
                            ft.Text(f"R$ {total_entradas:.2f}", size=15, color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD)
                        ]), padding=10
                    )
                )

                card_saidas = ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Text("Saídas", size=11, color=ft.colors.GREY_400), 
                            ft.Text(f"R$ {total_saidas:.2f}", size=15, color=ft.colors.RED_400, weight=ft.FontWeight.BOLD)
                        ]), padding=10
                    )
                )

                card_saldo = ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Text("Saldo", size=11, color=ft.colors.GREY_400), 
                            ft.Text(f"R$ {saldo:.2f}", size=15, color=ft.colors.BLUE_400, weight=ft.FontWeight.BOLD)
                        ]), padding=10
                    )
                )

                container_dashboard.controls.clear()
                container_dashboard.controls.extend([
                    ft.ResponsiveRow([
                        ft.Column([card_entradas], col={"xs": 12, "sm": 4}),
                        ft.Column([card_saidas], col={"xs": 12, "sm": 4}),
                        ft.Column([card_saldo], col={"xs": 12, "sm": 4}),
                    ]),
                    ft.Divider(),
                    ft.Text("Gastos Por Categoria", size=16, weight=ft.FontWeight.BOLD),
                    ft.ListView(controls=[tabela_categorias], expand=False)
                ])
                # REMOVIDO: page.update() precoce durante a montagem inicial

            def mes_anterior(e):
                primeiro_dia = data_referencia[0].replace(day=1)
                data_referencia[0] = primeiro_dia - timedelta(days=1)
                atualizar_relatorio_mensal()
                page.update()

            def mes_seguinte(e):
                proximo_mes = (data_referencia[0].replace(day=28) + timedelta(days=4)).replace(day=1)
                data_referencia[0] = proximo_mes
                atualizar_relatorio_mensal()
                page.update()

            seletor_mes_dinamico = ft.Row([
                ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=mes_anterior),
                texto_mes_ano,
                ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=mes_seguinte),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)

            atualizar_relatorio_mensal()

            return ft.Container(
                content=ft.Column([
                    ft.Text("Relatório Mensal", size=20, weight=ft.FontWeight.BOLD),
                    seletor_mes_dinamico,
                    ft.Divider(),
                    container_dashboard
                ], spacing=12), 
                padding=10
            )

        conteudo_central.controls.append(criar_tela_formulario())
        
        page.add(
            ft.Row(
                [
                    barra_lateral, 
                    ft.VerticalDivider(width=1), 
                    conteudo_central
                ], 
                expand=True
            )
        )
    except Exception as e:
        print(f"ERRO CRÍTICO NO FLET: {e}")
        raise e

app = flet_fastapi.app(main)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    # Passamos o objeto 'app' diretamente para evitar falhas de caminho de arquivo (Item 1)
    uvicorn.run(app, host="0.0.0.0", port=port)