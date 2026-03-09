#!/usr/bin/env python3
"""
Genio Admin CLI
Operational commands for managing the Genio platform
"""
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

@click.group()
@click.option('--api-url', default='http://localhost:8000', help='API base URL')
@click.option('--api-key', envvar='GENIO_API_KEY', help='Admin API key')
@click.pass_context
def cli(ctx, api_url: str, api_key: Optional[str]):
    """Genio Knowledge OS - Admin CLI"""
    ctx.ensure_object(dict)
    ctx.obj['api_url'] = api_url
    ctx.obj['api_key'] = api_key
    ctx.obj['headers'] = {'Authorization': f'Bearer {api_key}'} if api_key else {}


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    url = f"{ctx.obj['api_url']}/health"
    
    try:
        r = httpx.get(url, headers=ctx.obj['headers'], timeout=10)
        data = r.json()
        
        table = Table(title="System Health")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        for component, info in data.get('components', {}).items():
            status = "✅" if info.get('status') == 'healthy' else "❌"
            table.add_row(component, status, str(info.get('details', '')))
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--email', required=True, help='User email')
@click.option('--tier', type=click.Choice(['FREE', 'PROFESSIONAL', 'ENTERPRISE']), required=True)
@click.pass_context
def set_tier(ctx, email: str, tier: str):
    """Set user subscription tier"""
    url = f"{ctx.obj['api_url']}/admin/users/{email}/tier"
    
    try:
        r = httpx.post(url, json={'tier': tier}, headers=ctx.obj['headers'])
        if r.status_code == 200:
            console.print(f"[green]✓ Updated {email} to {tier}[/green]")
        else:
            console.print(f"[red]Error: {r.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--user-id', help='Filter by user ID')
@click.option('--limit', default=20, help='Number of results')
@click.pass_context
def list_users(ctx, user_id: Optional[str], limit: int):
    """List users"""
    url = f"{ctx.obj['api_url']}/admin/users"
    params = {'limit': limit}
    if user_id:
        params['user_id'] = user_id
    
    try:
        r = httpx.get(url, params=params, headers=ctx.obj['headers'])
        data = r.json()
        
        table = Table(title="Users")
        table.add_column("ID", style="dim")
        table.add_column("Email")
        table.add_column("Tier", style="cyan")
        table.add_column("Status")
        table.add_column("Created")
        
        for user in data.get('users', []):
            table.add_row(
                user['id'][:8] + '...',
                user['email'],
                user['tier'],
                '✅' if user['is_active'] else '❌',
                user['created_at'][:10]
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show platform statistics"""
    url = f"{ctx.obj['api_url']}/admin/stats"
    
    try:
        r = httpx.get(url, headers=ctx.obj['headers'])
        data = r.json()
        
        table = Table(title="Platform Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        metrics = [
            ("Total Users", data.get('total_users', 0)),
            ("Active Feeds", data.get('active_feeds', 0)),
            ("Articles Today", data.get('articles_today', 0)),
            ("Briefs Sent Today", data.get('briefs_sent_today', 0)),
            ("Avg AI Cost/User", f"${data.get('avg_ai_cost', 0):.2f}"),
            ("Qdrant Vectors", data.get('vector_count', 0)),
        ]
        
        for metric, value in metrics:
            table.add_row(metric, str(value))
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--feed-id', required=True, help='Feed ID to refresh')
@click.pass_context
def refresh_feed(ctx, feed_id: str):
    """Manually trigger feed refresh"""
    url = f"{ctx.obj['api_url']}/admin/feeds/{feed_id}/refresh"
    
    try:
        r = httpx.post(url, headers=ctx.obj['headers'])
        if r.status_code == 202:
            console.print(f"[green]✓ Feed refresh queued[/green]")
        else:
            console.print(f"[red]Error: {r.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--days', default=7, help='Days of history')
@click.pass_context
def ai_costs(ctx, days: int):
    """Show AI cost breakdown"""
    url = f"{ctx.obj['api_url']}/admin/ai-costs"
    
    try:
        r = httpx.get(url, params={'days': days}, headers=ctx.obj['headers'])
        data = r.json()
        
        table = Table(title=f"AI Costs (Last {days} days)")
        table.add_column("Date")
        table.add_column("Embeddings", justify="right")
        table.add_column("Summaries", justify="right")
        table.add_column("Scout", justify="right")
        table.add_column("Total", justify="right", style="green")
        
        for day in data.get('daily_costs', []):
            table.add_row(
                day['date'],
                f"${day['embeddings']:.2f}",
                f"${day['summaries']:.2f}",
                f"${day['scout']:.2f}",
                f"${day['total']:.2f}"
            )
        
        console.print(table)
        console.print(f"\n[bold]Total: ${data.get('total', 0):.2f}[/bold]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--threshold', default=0.9, help='Similarity threshold')
@click.option('--dry-run', is_flag=True, help='Preview without deleting')
@click.pass_context
def dedup(ctx, threshold: float, dry_run: bool):
    """Run deduplication on articles"""
    url = f"{ctx.obj['api_url']}/admin/dedup"
    
    try:
        r = httpx.post(url, json={
            'threshold': threshold,
            'dry_run': dry_run
        }, headers=ctx.obj['headers'])
        
        data = r.json()
        action = "Would remove" if dry_run else "Removed"
        console.print(f"[green]{action} {data.get('removed', 0)} duplicates[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('feature')
@click.option('--enable/--disable', default=True, help='Enable or disable')
@click.option('--percentage', type=int, help='Percentage rollout (0-100)')
@click.pass_context
def feature_flag(ctx, feature: str, enable: bool, percentage: Optional[int]):
    """Manage feature flags"""
    url = f"{ctx.obj['api_url']}/admin/feature-flags/{feature}"
    
    try:
        r = httpx.patch(url, json={
            'enabled': enable,
            'percentage': percentage
        }, headers=ctx.obj['headers'])
        
        if r.status_code == 200:
            status = "enabled" if enable else "disabled"
            console.print(f"[green]✓ Feature '{feature}' {status}[/green]")
        else:
            console.print(f"[red]Error: {r.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    cli()
