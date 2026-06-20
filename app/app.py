from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from portfolio_scraper.portfolio_analysis import (
    PORTFOLIO_COLUMNS,
    SCRAPERS,
    allocation_table,
    apply_holdings_filters,
    build_combined_holdings,
    compute_kpis,
    empty_portfolio,
    etf_exposure_figure,
    parse_portfolio_csv,
    pie_figure,
    portfolio_to_csv,
    sunburst_figure,
    top_holdings_bar_figure,
    world_map_figure,
)


def _to_dataframe(data: pd.DataFrame | list[list[object]] | None) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    else:
        frame = pd.DataFrame(data or [], columns=PORTFOLIO_COLUMNS)

    for column in PORTFOLIO_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    frame = frame[PORTFOLIO_COLUMNS]
    return frame


def _status_message(errors: list[str], rows: int) -> str:
    summary = f"✅ Analysis completed: {rows} holdings rows generated."
    if not errors:
        return summary
    joined = "\n".join(f"- {error}" for error in errors)
    return f"⚠️ {summary}\n\nWarnings:\n{joined}"


def _kpi_markdown(filtered_holdings: pd.DataFrame, valid_portfolio: pd.DataFrame) -> str:
    metrics = compute_kpis(filtered_holdings, valid_portfolio)
    distribution_country = allocation_table(filtered_holdings, "country").head(5)
    distribution_sector = allocation_table(filtered_holdings, "sector_group").head(5)
    distribution_asset = allocation_table(filtered_holdings, "asset_type").head(5)

    def _format_distribution(frame: pd.DataFrame, label: str) -> str:
        if frame.empty:
            return f"- {label}: n/a"
        first = frame.iloc[0]
        return (
            f"- Top {label}: {first[label]} "
            f"({first['weighted_portfolio_weight']:.2%}, € {first['estimated_value_eur']:,.2f})"
        )

    return "\n".join(
        [
            "### KPI",
            f"- Totale investito: **€ {metrics['total_invested']:,.2f}**",
            f"- Numero ETF: **{metrics['etf_count']}**",
            f"- Holdings unici (filtrati): **{metrics['unique_holdings']}**",
            f"- Righe holdings dopo filtri: **{metrics['rows_after_filters']}**",
            f"- Concentrazione Top 10 holdings: **{metrics['top_n_concentration']:.2%}**",
            "",
            "### Distribuzione (top categoria)",
            _format_distribution(distribution_country, "country"),
            _format_distribution(distribution_sector, "sector_group"),
            _format_distribution(distribution_asset, "asset_type"),
        ]
    )


def _table_for_display(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return holdings

    table = holdings.copy()
    table["weight_in_etf"] = pd.to_numeric(table["weight_in_etf"], errors="coerce")
    table["weighted_portfolio_weight"] = pd.to_numeric(
        table["weighted_portfolio_weight"], errors="coerce"
    )
    table["estimated_value_eur"] = pd.to_numeric(table["estimated_value_eur"], errors="coerce")
    return table


def _filter_choices(holdings: pd.DataFrame, column: str) -> list[str]:
    if holdings.empty or column not in holdings.columns:
        return []
    return sorted([value for value in holdings[column].dropna().unique().tolist() if str(value).strip()])


def add_row(portfolio_data: pd.DataFrame | list[list[object]] | None, isin: str, scraper: str, investment: float):
    portfolio = _to_dataframe(portfolio_data)
    next_row = pd.DataFrame(
        [
            {
                "isin": (isin or "").strip().upper(),
                "scraper": scraper or "",
                "investment_eur": investment if investment is not None else "",
            }
        ]
    )
    updated = pd.concat([portfolio, next_row], ignore_index=True)
    return updated, updated, "Riga aggiunta."


def remove_row(portfolio_data: pd.DataFrame | list[list[object]] | None, row_number: float):
    portfolio = _to_dataframe(portfolio_data)
    if portfolio.empty:
        return portfolio, portfolio, "Nessuna riga da rimuovere."

    if row_number is None:
        return portfolio, portfolio, "Inserisci l'indice riga da rimuovere (1-based)."

    idx = int(row_number) - 1
    if idx < 0 or idx >= len(portfolio):
        return portfolio, portfolio, f"Indice riga non valido: {int(row_number)}"

    updated = portfolio.drop(index=idx).reset_index(drop=True)
    return updated, updated, f"Riga {int(row_number)} rimossa."


def import_portfolio(file_path: str | None):
    if file_path is None:
        empty = empty_portfolio()
        return empty, empty, "Nessun file selezionato."

    try:
        imported = parse_portfolio_csv(file_path)
        return imported, imported, f"Import completato: {len(imported)} righe."
    except ValueError as error:
        current = empty_portfolio()
        return current, current, f"Errore CSV: {error}"


def export_portfolio(portfolio_data: pd.DataFrame | list[list[object]] | None):
    portfolio = _to_dataframe(portfolio_data)
    csv_data = portfolio_to_csv(portfolio)
    output = Path(tempfile.gettempdir()) / "portfolio_etf_export.csv"
    output.write_bytes(csv_data)
    return str(output), "Export completato."


def analyze_portfolio(portfolio_data: pd.DataFrame | list[list[object]] | None):
    portfolio = _to_dataframe(portfolio_data)
    combined, errors, valid_portfolio = build_combined_holdings(portfolio)

    if combined.empty:
        message = "\n".join(errors) if errors else "Nessun dato holdings disponibile."
        empty = pd.DataFrame()
        empty_multiselect = gr.update(choices=[], value=[])
        empty_plot = None
        return (
            empty,
            empty,
            valid_portfolio,
            message,
            "### KPI\n- Nessun dato disponibile.",
            empty_plot,
            empty_plot,
            empty_plot,
            empty_plot,
            empty_plot,
            empty_plot,
            empty_multiselect,
            empty_multiselect,
            empty_multiselect,
            empty_multiselect,
        )

    filtered = combined
    table = _table_for_display(filtered)
    status = _status_message(errors, len(combined))
    kpi = _kpi_markdown(filtered, valid_portfolio)

    return (
        combined,
        table,
        valid_portfolio,
        status,
        kpi,
        pie_figure(filtered, "country", "Composizione geografica"),
        pie_figure(filtered, "sector_group", "Composizione per settore"),
        pie_figure(filtered, "asset_type", "Composizione per tipo asset"),
        world_map_figure(filtered),
        top_holdings_bar_figure(filtered),
        sunburst_figure(filtered),
        gr.update(choices=_filter_choices(combined, "etf_isin"), value=[]),
        gr.update(choices=_filter_choices(combined, "country"), value=[]),
        gr.update(choices=_filter_choices(combined, "sector_group"), value=[]),
        gr.update(choices=_filter_choices(combined, "asset_type"), value=[]),
    )


def apply_filters(
    holdings_state: pd.DataFrame,
    valid_portfolio: pd.DataFrame,
    search_text: str,
    etf_isins: list[str],
    countries: list[str],
    sectors: list[str],
    asset_types: list[str],
):
    filtered = apply_holdings_filters(
        holdings_state if isinstance(holdings_state, pd.DataFrame) else pd.DataFrame(),
        search_text,
        etf_isins or [],
        countries or [],
        sectors or [],
        asset_types or [],
    )
    table = _table_for_display(filtered)
    kpi = _kpi_markdown(
        filtered,
        valid_portfolio if isinstance(valid_portfolio, pd.DataFrame) else empty_portfolio(),
    )
    return (
        table,
        kpi,
        pie_figure(filtered, "country", "Composizione geografica"),
        pie_figure(filtered, "sector_group", "Composizione per settore"),
        pie_figure(filtered, "asset_type", "Composizione per tipo asset"),
        world_map_figure(filtered),
        top_holdings_bar_figure(filtered),
        sunburst_figure(filtered),
        etf_exposure_figure(filtered),
    )


def build_app() -> gr.Blocks:
    with gr.Blocks(title="ETF Portfolio Analyzer (Gradio)") as demo:
        gr.Markdown(
            """
            # ETF Portfolio Analyzer (Gradio)
            Inserisci il portfolio ETF, importa/esporta CSV e analizza holdings aggregati.
            """
        )

        portfolio_state = gr.State(empty_portfolio())
        holdings_state = gr.State(pd.DataFrame())
        valid_portfolio_state = gr.State(empty_portfolio())

        with gr.Tab("Portfolio ETF"):
            portfolio_table = gr.Dataframe(
                headers=PORTFOLIO_COLUMNS,
                datatype=["str", "str", "number"],
                value=empty_portfolio(),
                row_count=(1, "dynamic"),
                column_count=(3, "fixed"),
                interactive=True,
                label="Portfolio (isin, scraper, investment_eur)",
            )

            with gr.Row():
                isin_input = gr.Textbox(label="ISIN")
                scraper_input = gr.Dropdown(
                    choices=list(SCRAPERS.keys()),
                    label="Scraper",
                    value=list(SCRAPERS.keys())[0],
                )
                investment_input = gr.Number(label="Investment EUR", value=0.0, minimum=0)
                add_btn = gr.Button("Aggiungi riga")

            with gr.Row():
                remove_index = gr.Number(label="Rimuovi riga #", value=1, minimum=1, precision=0)
                remove_btn = gr.Button("Rimuovi")
                export_btn = gr.Button("Esporta CSV")

            with gr.Row():
                import_file = gr.File(label="Importa CSV", file_types=[".csv"])
                download_file = gr.File(label="File CSV esportato")

            portfolio_status = gr.Markdown()

        with gr.Tab("Analisi holdings"):
            analyze_btn = gr.Button("Analizza portfolio", variant="primary")
            analysis_status = gr.Markdown()

            with gr.Row():
                search_text = gr.Textbox(label="Filtro testuale (nome/ISIN)")
                filter_etf = gr.Dropdown(label="Filtro ETF", multiselect=True, choices=[])
                filter_country = gr.Dropdown(label="Filtro Paese", multiselect=True, choices=[])
                filter_sector = gr.Dropdown(label="Filtro Settore", multiselect=True, choices=[])
                filter_asset = gr.Dropdown(label="Filtro Asset Type", multiselect=True, choices=[])

            apply_filter_btn = gr.Button("Applica filtri")

            kpi_markdown = gr.Markdown("### KPI\n- In attesa di analisi.")
            holdings_table = gr.Dataframe(label="Holdings filtrati", interactive=False)

            with gr.Row():
                geography_pie = gr.Plot(label="Geografia")
                sector_pie = gr.Plot(label="Settore")
                asset_pie = gr.Plot(label="Tipo asset")

            with gr.Row():
                world_map = gr.Plot(label="Mappa globale")
                top_holdings = gr.Plot(label="Top holdings")

            with gr.Row():
                sunburst = gr.Plot(label="Sunburst")
                etf_exposure = gr.Plot(label="Exposure per ETF")

        portfolio_table.change(
            fn=lambda df: (_to_dataframe(df), "Tabella aggiornata."),
            inputs=[portfolio_table],
            outputs=[portfolio_state, portfolio_status],
        )

        add_btn.click(
            fn=add_row,
            inputs=[portfolio_table, isin_input, scraper_input, investment_input],
            outputs=[portfolio_table, portfolio_state, portfolio_status],
        )

        remove_btn.click(
            fn=remove_row,
            inputs=[portfolio_table, remove_index],
            outputs=[portfolio_table, portfolio_state, portfolio_status],
        )

        import_file.change(
            fn=import_portfolio,
            inputs=[import_file],
            outputs=[portfolio_table, portfolio_state, portfolio_status],
        )

        export_btn.click(
            fn=export_portfolio,
            inputs=[portfolio_table],
            outputs=[download_file, portfolio_status],
        )

        analyze_btn.click(
            fn=analyze_portfolio,
            inputs=[portfolio_table],
            outputs=[
                holdings_state,
                holdings_table,
                valid_portfolio_state,
                analysis_status,
                kpi_markdown,
                geography_pie,
                sector_pie,
                asset_pie,
                world_map,
                top_holdings,
                sunburst,
                filter_etf,
                filter_country,
                filter_sector,
                filter_asset,
            ],
        ).then(
            fn=lambda holdings: etf_exposure_figure(
                holdings if isinstance(holdings, pd.DataFrame) else pd.DataFrame()
            ),
            inputs=[holdings_state],
            outputs=[etf_exposure],
        )

        apply_filter_btn.click(
            fn=apply_filters,
            inputs=[
                holdings_state,
                valid_portfolio_state,
                search_text,
                filter_etf,
                filter_country,
                filter_sector,
                filter_asset,
            ],
            outputs=[
                holdings_table,
                kpi_markdown,
                geography_pie,
                sector_pie,
                asset_pie,
                world_map,
                top_holdings,
                sunburst,
                etf_exposure,
            ],
        )

    return demo


if __name__ == "__main__":
    build_app().queue().launch()
