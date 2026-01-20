# console_printer.py
"""
Module for console output formatting and display.
"""

from typing import Any, ClassVar

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from google_sheets_llm_analyzer_package.config import AppConfig
from google_sheets_llm_analyzer_package.data_analyzer import AnalysisResult


class ConsolePrinter:
    """Handles all console output operations."""

    BANNER = "\n".join(
        [
            "🤖 Google Sheets LLM Analyzer",
            "📊 Statistical Data Analysis",
        ]
    )

    PRIORITY_STYLES: ClassVar[dict] = {
        "high": (
            "🔴",
            "bold red",
        ),
        "medium": (
            "🟡",
            "bold yellow",
        ),
        "low": (
            "🟢",
            "bold green",
        ),
    }

    def __init__(self):
        """Initialize console printer."""
        self.console = Console()

    def print_banner(self):
        """Display application banner."""
        self.console.print(
            Panel(
                "",
                subtitle=self.BANNER,
                expand=True,
                style="bold blue",
            ),
            justify="full",
        )

    def print_config_summary(self, config: AppConfig):
        """Display configuration summary."""
        self.console.print(
            Panel.fit(
                "[bold]System Configuration[/bold]",
                border_style="cyan",
            ),
        )

        table = Table(
            show_header=False,
            box=None,
        )
        table.add_column(
            "Parameter",
            style="cyan",
        )
        table.add_column(
            "Value",
            style="green",
        )

        table.add_row(
            "Google Sheet",
            config.spreadsheet_id,
        )
        table.add_row(
            "Sheet",
            config.sheet_name,
        )
        table.add_row(
            "Category Column",
            f"Column {config.category_column}",
        )
        table.add_row(
            "LLM Key",
            "Provided" if config.is_llm_enabled else "Not provided",
        )
        table.add_row(
            "Debug Mode",
            "Yes" if config.debug else "No",
        )

        self.console.print(
            table,
            end="\n\n",
        )

    def print_statistics(
        self,
        result: AnalysisResult,
        llm_results: list[dict[str, Any]] | None = None,
    ):
        """
        Display statistics in a formatted way.
        """
        if not result.has_data:
            self.console.print(
                Panel(
                    "[yellow]📭 No data for analysis[/yellow]",
                    border_style="yellow",
                ),
                end="\n\n",
            )
            return

        # Print main statistics
        self._print_main_stats(result)

        # Print summary
        self._print_summary(result)

        # Print LLM analysis if available
        if llm_results:
            self._print_llm_analysis(llm_results)

    def _print_main_stats(self, result: AnalysisResult):
        """Print main statistics table."""
        self.console.print(
            Panel(
                "[bold]📈 Request Statistics[/bold]",
                expand=False,
                border_style="magenta",
            ),
            end="\n\n",
        )

        table = Table(
            show_header=True,
            box=ROUNDED,
        )
        table.add_column(
            "Category",
            style="cyan",
            no_wrap=True,
        )
        table.add_column(
            "Count",
            justify="right",
            style="green",
        )
        table.add_column(
            "Percentage",
            justify="right",
            style="yellow",
        )

        for category, count in result.categories_sorted:
            percent = self._format_percentage(
                count,
                result.total_requests,
            )
            table.add_row(
                category,
                str(count),
                f"{percent}%",
            )

        self.console.print(
            table,
            end="\n\n",
        )

    def _print_summary(self, result: AnalysisResult):
        """Print summary table."""
        total = result.total_requests

        table = Table(
            show_header=False,
            box=None,
            expand=False,
        )
        table.add_column(
            "Metric",
            style="cyan",
        )
        table.add_column(
            "Value",
            style="green",
        )

        table.add_row(
            "Total Requests",
            str(result.total_requests),
        )
        table.add_row(
            "Unique Categories",
            str(len(result.category_counts)),
        )

        if result.most_common_category:
            percent = self._format_percentage(
                result.most_common_count,
                total,
            )
            table.add_row(
                "Most Popular Category",
                f"[bold]{result.most_common_category}[/bold] "
                f"({result.most_common_count} requests, "
                f"{percent}%)",
            )

        self.console.print(
            Panel(
                table,
                border_style="green",
                expand=False,
            ),
            end="\n\n",
        )

    def _print_llm_analysis(self, llm_results: list[dict[str, Any]]):
        """Print LLM analysis results."""
        self.console.print(
            Panel(
                "[bold]🤖 LLM Analysis[/bold]",
                border_style="blue",
                expand=False,
            ),
            end="\n\n",
        )

        for request in llm_results:
            if request.get("llm_analysis"):
                self._print_single_request_analysis(request)

        self.console.print(
            f"[dim]Total analyzed requests: {len(llm_results)}[/dim]",
            end="\n\n",
        )

    def _print_single_request_analysis(self, request: dict[str, Any]):
        """Print analysis for a single request."""
        analysis = request["llm_analysis"]
        emoji, style = self.PRIORITY_STYLES.get(
            analysis.priority,
            (
                "⚪",
                "bold white",
            ),
        )

        self.console.print(
            f"{emoji} [bold]Request #{request['row_number']}[/bold] "
            f"(ID: {request['id']})",
            end="\n\n",
        )

        # Print details table
        self._print_request_details(
            request,
            analysis,
            style,
        )

        # Print summary and recommendation
        if analysis.summary:
            self.console.print(
                "   [dim]📝 Summary:[/dim] "
                f"[italic]{analysis.summary}[/italic]",
                end="\n\n",
            )

        if analysis.recommendation:
            self.console.print(
                f"   [dim]💡 Recommendation:[/dim] {analysis.recommendation}",
                end="\n\n",
            )

    def _print_request_details(
        self,
        request: dict[str, Any],
        analysis: Any,
        style: str,
    ):
        """Print request details table."""
        table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            expand=False,
        )
        table.add_column(
            "Field",
            style="dim",
        )
        table.add_column(
            "Value",
            style="white",
        )

        table.add_row(
            "Category",
            request.get("category", "Not specified"),
        )
        table.add_row(
            "Date",
            request.get("date", "Not specified"),
        )
        table.add_row(
            "Choice",
            request.get("choice", "Not specified"),
        )
        table.add_row(
            "Priority",
            f"[{style}]{analysis.priority_text}[/{style}]",
        )
        table.add_row(
            "Analysis Time",
            f"{analysis.processing_time:.2f} sec",
        )

        self.console.print(
            table,
            end="\n\n",
        )

    @staticmethod
    def _format_percentage(
        count: int,
        total: int,
    ) -> str:
        """Format percentage with one decimal place."""
        if total == 0:
            return "0.0"
        return f"{(count / total) * 100:.1f}"

    def print_error(
        self,
        message: str,
        show_exception: bool = False,
    ):
        """Print error message."""
        self.console.print(f"[red]❌ {message}[/red]")
        if show_exception:
            self.console.print_exception()

    def print_warning(self, message: str):
        """Print warning message."""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def print_success(self, message: str):
        """Print success message."""
        self.console.print(f"[green]✅ {message}[/green]")

    def print_info(self, message: str):
        """Print info message."""
        self.console.print(f"[blue]ℹ️  {message}[/blue]")

    def print_completion_summary(
        self,
        success: bool,
        total_requests: int,
        llm_enabled: bool,
        llm_analyzed: int = 0,
    ):
        """Print analysis completion summary."""
        if llm_enabled:
            llm_status = f"✅ Analyzed {llm_analyzed} requests"
        else:
            llm_status = "❌ Disabled"

        if success:
            self.console.print(
                Panel.fit(
                    f"[green]✅ Analysis completed successfully![/green]\n"
                    f"Processed requests: {total_requests}\n"
                    f"LLM analysis: {llm_status}",
                    border_style="green",
                ),
            )
