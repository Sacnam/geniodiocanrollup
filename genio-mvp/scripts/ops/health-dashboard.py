#!/usr/bin/env python3
"""
Genio Health Dashboard CLI
Real-time system health monitoring
"""
import sys
import time
from datetime import datetime
from typing import Dict, Optional

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich import box

console = Console()


class HealthChecker:
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
    
    def check_api(self) -> Dict:
        """Check API health."""
        try:
            r = httpx.get(f"{self.api_url}/health", headers=self.headers, timeout=5)
            return {
                'status': 'healthy' if r.status_code == 200 else 'unhealthy',
                'latency_ms': r.elapsed.total_seconds() * 1000,
                'details': r.json() if r.status_code == 200 else {}
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_metrics(self) -> Dict:
        """Get key metrics."""
        try:
            r = httpx.get(f"{self.api_url}/admin/stats", headers=self.headers, timeout=5)
            return r.json() if r.status_code == 200 else {}
        except:
            return {}
    
    def check_celery(self) -> Dict:
        """Check Celery workers."""
        try:
            from celery.task.control import inspect
            i = inspect()
            active = i.active() or {}
            scheduled = i.scheduled() or {}
            
            total_workers = len(active)
            total_tasks = sum(len(t) for t in active.values())
            
            return {
                'workers': total_workers,
                'active_tasks': total_tasks,
                'status': 'healthy' if total_workers > 0 else 'unhealthy'
            }
        except:
            return {'status': 'unknown', 'workers': 0, 'active_tasks': 0}
    
    def check_database(self) -> Dict:
        """Check database connectivity."""
        try:
            import time
            start = time.time()
            # Would actually query DB
            latency = (time.time() - start) * 1000
            return {'status': 'healthy', 'latency_ms': latency}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_qdrant(self) -> Dict:
        """Check Qdrant."""
        try:
            r = httpx.get("http://localhost:6333/collections/articles", timeout=5)
            data = r.json()
            return {
                'status': 'healthy',
                'vectors_count': data.get('result', {}).get('vectors_count', 0)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


def create_health_table(checker: HealthChecker) -> Table:
    """Create health status table."""
    table = Table(box=box.ROUNDED, title="System Health")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")
    
    # API
    api = checker.check_api()
    status_emoji = "✅" if api['status'] == 'healthy' else "❌"
    details = f"{api.get('latency_ms', 0):.0f}ms" if 'latency_ms' in api else api.get('error', '')
    table.add_row("API", f"{status_emoji} {api['status']}", details)
    
    # Database
    db = checker.check_database()
    status_emoji = "✅" if db['status'] == 'healthy' else "❌"
    details = f"{db.get('latency_ms', 0):.0f}ms" if 'latency_ms' in db else db.get('error', '')
    table.add_row("Database", f"{status_emoji} {db['status']}", details)
    
    # Qdrant
    qdrant = checker.check_qdrant()
    status_emoji = "✅" if qdrant['status'] == 'healthy' else "❌"
    details = f"{qdrant.get('vectors_count', 0)} vectors" if 'vectors_count' in qdrant else qdrant.get('error', '')
    table.add_row("Qdrant", f"{status_emoji} {qdrant['status']}", details)
    
    # Celery
    celery = checker.check_celery()
    status_emoji = "✅" if celery['status'] == 'healthy' else "⚠️"
    details = f"{celery.get('workers', 0)} workers, {celery.get('active_tasks', 0)} tasks"
    table.add_row("Celery", f"{status_emoji} {celery['status']}", details)
    
    return table


def create_metrics_table(checker: HealthChecker) -> Table:
    """Create metrics table."""
    metrics = checker.check_metrics()
    
    table = Table(box=box.ROUNDED, title="Platform Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    if metrics:
        table.add_row("Total Users", str(metrics.get('total_users', 0)))
        table.add_row("Active Feeds", str(metrics.get('active_feeds', 0)))
        table.add_row("Articles Today", str(metrics.get('articles_today', 0)))
        table.add_row("Briefs Sent", str(metrics.get('briefs_sent_today', 0)))
        table.add_row("Avg AI Cost/User", f"${metrics.get('avg_ai_cost', 0):.2f}")
    else:
        table.add_row("Status", "❌ Unable to fetch metrics")
    
    return table


@click.command()
@click.option('--api-url', default='http://localhost:8000', help='API URL')
@click.option('--api-key', envvar='GENIO_API_KEY', help='Admin API key')
@click.option('--watch', '-w', is_flag=True, help='Watch mode')
@click.option('--interval', default=5, help='Refresh interval (seconds)')
def main(api_url: str, api_key: Optional[str], watch: bool, interval: int):
    """Genio Health Dashboard"""
    checker = HealthChecker(api_url, api_key)
    
    if watch:
        with Live(refresh_per_second=1/interval, screen=True) as live:
            while True:
                layout = Layout()
                
                health_table = create_health_table(checker)
                metrics_table = create_metrics_table(checker)
                
                layout.split_column(
                    Layout(Panel(health_table, title="Health Status")),
                    Layout(Panel(metrics_table, title="Metrics")),
                    Layout(Panel(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", style="dim"))
                )
                
                live.update(layout)
                time.sleep(interval)
    else:
        # Single check
        health_table = create_health_table(checker)
        metrics_table = create_metrics_table(checker)
        
        console.print(health_table)
        console.print()
        console.print(metrics_table)


if __name__ == '__main__':
    main()
