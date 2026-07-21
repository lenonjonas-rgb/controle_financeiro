import flet as ft
import sqlite3
from datetime import datetime, timedelta
import os

# ==========================================
# 1. BANCO DE DADOS (PERSISTÊNCIA & MEMÓRIA)
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
# 2. APLICAÇÃO VISUAL (FLET DASHBOARD RESPONSIVO)
# ==========================================
def main(page: ft.Page):
    page.title = "Controle Financeiro - Gestão & Gráficos"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    inicializar_banco()

    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # ------------------------------------------
    # CAMPOS DO FORMULÁRIO DE CADASTRO
    # ------------------------------------------
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

    def data_selecionada_calendario(e):
        if e.control.value:
            input_data.value = e.control.value.strftime("%d/%m/%Y")
            input_data.update()

    date_picker = ft.DatePicker(on_change=data_selecionada_calendario)
    page.overlay.append(date_picker)

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

    # ------------------------------------------
    # SALVAMENTO
    # ------------------------------------------
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

    def mostrar_snack(mensagem):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem))
        page.snack_bar.open = True
        page.update()

    # ------------------------------------------
    # NAVEGAÇÃO RESPONSIVA
    # ------------------------------------------
    def mudar_tela_interface(indice_aba):
        if barra_lateral:
            barra_lateral.selected_index = indice_aba
            barra_lateral.update()
        if barra_inferior:
            barra_inferior.selected_index = indice_aba
            barra_inferior.update()

        conteudo_central.controls.clear()
        
        if indice_aba == 0:
            conteudo_central.controls.append(criar_tela_formulario())
        elif indice_aba == 1:
            conteudo_central.controls.append(criar_tela_relatorio())
            
        page.update()

    # Menu Lateral para Computadores
    barra_lateral = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.ADD_CARD, label="Novo"),
            ft.NavigationRailDestination(icon=ft.icons.ANALYTICS, label="Relatórios"),
        ],
        on_change=lambda e: mudar_tela_interface(e.control.selected_index),
    )

    # Menu Inferior para Celulares
    barra_inferior = ft.NavigationBar(
        selected_index=0,
        destinations=[
            ft.NavigationDestination(icon=ft.icons.ADD_CARD, label="Novo Lançamento"),
            ft.NavigationDestination(icon=ft.icons.ANALYTICS, label="Relatórios"),
        ],
        on_change=lambda e: mudar_tela_interface(e.control.selected_index),
    )

    conteudo_central = ft.Column(expand=True, alignment=ft.MainAxisAlignment.START)

    # ------------------------------------------
    # TELA 1: CADASTRO RESPONSIVO
    # ------------------------------------------
    def criar_tela_formulario():
        return ft.Container(
            content=ft.Column([
                ft.Text("Novo Lançamento Financeiro", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Preencha os dados da transação abaixo.", size=13, color=ft.colors.GREY_400),
                ft.Divider(),
                
                # Bloco de Data e Atalhos (Responsivo)
                ft.ResponsiveRow([
                    ft.Column([input_data], col={"xs": 12, "sm": 6}),
                    ft.Column([
                        ft.Row([
                            ft.OutlinedButton("Hoje", on_click=set_data_hoje),
                            ft.OutlinedButton("Ontem", on_click=set_data_ontem),
                            ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda _: date_picker.pick_date()),
                        ], alignment=ft.MainAxisAlignment.START)
                    ], col={"xs": 12, "sm": 6}),
                ]),
                
                # Bloco de Tipo e Categoria
                ft.ResponsiveRow([
                    ft.Column([input_tipo], col={"xs": 12, "sm": 6}),
                    ft.Column([input_categoria], col={"xs": 12, "sm": 6}),
                ]),

                # Bloco do Valor
                ft.ResponsiveRow([
                    ft.Column([input_valor], col={"xs": 12, "sm": 6}),
                ]),
                
                # Bloco de Empresa e Histórico
                ft.ResponsiveRow([
                    ft.Column([input_empresa], col={"xs": 12, "sm": 7}),
                    ft.Column([dropdown_empresas], col={"xs": 12, "sm": 5}),
                ]),
                
                ft.Container(height=15),
                
                # Botão Salvar (Largura total no celular)
                ft.ResponsiveRow([
                    ft.Column([
                        ft.ElevatedButton(
                            "Salvar e Arquivar Lançamento", 
                            icon=ft.icons.SAVE, 
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.GREEN_700,
                                color=ft.colors.WHITE,
                                padding=20
                            ),
                            on_click=executar_salvamento,
                            width=1000
                        )
                    ], col={"xs": 12})
                ])
            ], spacing=15),
            padding=15
        )

    # ------------------------------------------
    # TELA 2: RELATÓRIOS MENSAIS RESPONSIVOS
    # ------------------------------------------
    def criar_tela_relatorio():
        data_referencia = [datetime.now()]

        meses_extenso = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        texto_mes_ano = ft.Text(
            f"{meses_extenso[data_referencia[0].month - 1]} / {data_referencia[0].year}", 
            size=18, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_200
        )

        container_dashboard = ft.Column(spacing=20)

        def abrir_detalhes_movimentacao(tipo_desejado, titulo_modal, cor_titulo):
            mes_ano = data_referencia[0].strftime("%m/%Y")
            
            conexao = sqlite3.connect("banco_financeiro.db")
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT id, data, empresa, categoria, valor 
                FROM lancamentos 
                WHERE tipo = ? AND data LIKE ? 
                ORDER BY id DESC
            """, (tipo_desejado, f"%/{mes_ano}"))
            
            registros = cursor.fetchall()
            conexao.close()

            def fechar_dialogo(e):
                dialog.open = False
                page.update()

            def remover_e_recarregar(e, reg_id):
                deletar_lancamento(reg_id)
                dialog.open = False
                page.update()
                atualizar_relatorio_mensal()
                mostrar_snack("Lançamento excluído com sucesso!")

            linhas_detalhes = []
            for r_id, dt, emp, cat, val in registros:
                linhas_detalhes.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(dt)),
                        ft.DataCell(ft.Text(emp)),
                        ft.DataCell(ft.Text(cat)),
                        ft.DataCell(ft.Text(f"R$ {val:.2f}", color=cor_titulo, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE, 
                                icon_color=ft.colors.RED_400,
                                tooltip="Excluir Lançamento",
                                on_click=lambda e, id_act=r_id: remover_e_recarregar(e, id_act)
                            )
                        )
                    ])
                )

            tabela_detalhes = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data")),
                    ft.DataColumn(ft.Text("Empresa")),
                    ft.DataColumn(ft.Text("Categoria")),
                    ft.DataColumn(ft.Text("Valor")),
                    ft.DataColumn(ft.Text("Ação")),
                ],
                rows=linhas_detalhes
            )

            dialog = ft.AlertDialog(
                title=ft.Text(f"{titulo_modal} ({mes_ano})", color=cor_titulo, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.ListView(controls=[tabela_detalhes], expand=True),
                    width=650,
                    height=350,
                ),
                actions=[
                    ft.TextButton("Fechar", on_click=fechar_dialogo)
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.open(dialog)

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
            secoes_grafico = []
            
            cores_grafico = [
                ft.colors.BLUE_400, ft.colors.RED_400, ft.colors.GREEN_400, 
                ft.colors.ORANGE_400, ft.colors.PURPLE_400, ft.colors.CYAN_400, 
                ft.colors.PINK_400, ft.colors.YELLOW_400
            ]

            for index, (cat, valor_total) in enumerate(gastos_por_categoria.items()):
                cor = cores_grafico[index % len(cores_grafico)]
                porcentagem = (valor_total / total_saidas * 100) if total_saidas > 0 else 0
                
                linhas_categoria.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(cat, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"R$ {valor_total:.2f}")),
                        ft.DataCell(ft.Text(f"{porcentagem:.1f}%", color=cor)),
                    ])
                )

                secoes_grafico.append(
                    ft.PieChartSection(
                        value=valor_total,
                        title=f"{porcentagem:.0f}%",
                        color=cor,
                        radius=40,
                        title_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
                    )
                )

            tabela_categorias = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Categoria")),
                    ft.DataColumn(ft.Text("Total")),
                    ft.DataColumn(ft.Text("%")),
                ],
                rows=linhas_categoria
            )

            grafico_pizza = ft.PieChart(
                sections=secoes_grafico if secoes_grafico else [ft.PieChartSection(1, title="Sem dados", color=ft.colors.GREY_700)],
                sections_space=2,
                center_space_radius=30,
                expand=True
            )

            # Cards de resumo com clique
            card_entradas = ft.Container(
                on_click=lambda _: abrir_detalhes_movimentacao("entrada", "Detalhamento de Entradas", ft.colors.GREEN_400),
                ink=True,
                content=ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Text("Entradas (Clique)", size=11, color=ft.colors.GREY_400), 
                            ft.Text(f"R$ {total_entradas:.2f}", size=16, color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD)
                        ]), padding=12
                    )
                )
            )

            card_saidas = ft.Container(
                on_click=lambda _: abrir_detalhes_movimentacao("saida", "Detalhamento de Saídas", ft.colors.RED_400),
                ink=True,
                content=ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Text("Saídas (Clique)", size=11, color=ft.colors.GREY_400), 
                            ft.Text(f"R$ {total_saidas:.2f}", size=16, color=ft.colors.RED_400, weight=ft.FontWeight.BOLD)
                        ]), padding=12
                    )
                )
            )

            card_saldo = ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text("Saldo do Mês", size=11, color=ft.colors.GREY_400), 
                        ft.Text(f"R$ {saldo:.2f}", size=16, color=ft.colors.BLUE_400, weight=ft.FontWeight.BOLD)
                    ]), padding=12
                )
            )

            container_dashboard.controls.clear()
            container_dashboard.controls.extend([
                # Cards do topo em grid adaptativo
                ft.ResponsiveRow([
                    ft.Column([card_entradas], col={"xs": 12, "sm": 4}),
                    ft.Column([card_saidas], col={"xs": 12, "sm": 4}),
                    ft.Column([card_saldo], col={"xs": 12, "sm": 4}),
                ]),
                ft.Divider(),
                ft.Text("Gastos Por Categoria", size=18, weight=ft.FontWeight.BOLD),
                
                # Tabela + Gráfico empilhados no celular
                ft.ResponsiveRow([
                    ft.Column([
                        ft.ListView(controls=[tabela_categorias], expand=False)
                    ], col={"xs": 12, "sm": 7}),
                    ft.Column([
                        ft.Container(content=grafico_pizza, height=200, alignment=ft.alignment.center)
                    ], col={"xs": 12, "sm": 5}),
                ])
            ])
            
            if page:
                page.update()

        # Navegação de Meses
        def mes_anterior(e):
            primeiro_dia = data_referencia[0].replace(day=1)
            data_referencia[0] = primeiro_dia - timedelta(days=1)
            atualizar_relatorio_mensal()

        def mes_seguinte(e):
            proximo_mes = (data_referencia[0].replace(day=28) + timedelta(days=4)).replace(day=1)
            data_referencia[0] = proximo_mes
            atualizar_relatorio_mensal()

        def ir_para_mes_atual(e):
            data_referencia[0] = datetime.now()
            atualizar_relatorio_mensal()

        seletor_mes_dinamico = ft.Row([
            ft.IconButton(icon=ft.icons.CHEVRON_LEFT, tooltip="Mês Anterior", on_click=mes_anterior),
            texto_mes_ano,
            ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, tooltip="Próximo Mês", on_click=mes_seguinte),
            ft.OutlinedButton("Atual", on_click=ir_para_mes_atual)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, wrap=True)

        atualizar_relatorio_mensal()

        return ft.Container(
            content=ft.Column([
                ft.Text("Relatório Mensal", size=22, weight=ft.FontWeight.BOLD),
                seletor_mes_dinamico,
                ft.Divider(),
                container_dashboard
            ], spacing=15), 
            padding=15
        )

    # Inicialização da Layout da Página
    conteudo_central.controls.append(criar_tela_formulario())
    
    # Renderização Adaptativa: Se for tela pequena usa navegação inferior, se for grande usa lateral
    def reordenar_layout():
        page.controls.clear()
        if page.width and page.width < 600:
            page.navigation_bar = barra_inferior
            page.add(conteudo_central)
        else:
            page.navigation_bar = None
            page.add(ft.Row([barra_lateral, ft.VerticalDivider(width=1), conteudo_central], expand=True))
        page.update()

    page.on_resize = lambda e: reordenar_layout()
    reordenar_layout()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")