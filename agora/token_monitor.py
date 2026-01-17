"""
Token Monitoring and Budget Management for Agora
=================================================
Real-time token usage tracking, budget enforcement, and cost analytics.

Usage:
    from agora.token_monitor import TokenMonitor, BudgetAlertSystem
    
    monitor = TokenMonitor(supabase_client, org_id="org-123")
    monitor.set_budget(project_id="proj-456", monthly_limit=100000)
    
    status = await monitor.check_budget("proj-456")
    if status['status'] == 'exceeded':
        raise Exception("Budget exceeded!")
"""

from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import asyncio


class TokenMonitor:
    """
    Real-time token usage monitoring and budget enforcement.
    
    Features:
    - Track token usage across projects
    - Set monthly/daily budgets
    - Get cost breakdowns by workflow and model
    - Real-time budget status checks
    """
    
    def __init__(self, supabase_client, org_id: str):
        """
        Initialize token monitor.
        
        Args:
            supabase_client: Supabase client instance
            org_id: Organization ID to monitor
        """
        self.client = supabase_client
        self.org_id = org_id
        self.budget_limits: Dict[str, int] = {}
        self.daily_limits: Dict[str, int] = {}
        
    def set_budget(self, project_id: str, monthly_limit: int, daily_limit: Optional[int] = None):
        """
        Set token budget limits for a project.
        
        Args:
            project_id: Project UUID
            monthly_limit: Maximum tokens per month
            daily_limit: Optional maximum tokens per day
        """
        self.budget_limits[project_id] = monthly_limit
        if daily_limit:
            self.daily_limits[project_id] = daily_limit
            
    async def check_budget(self, project_id: str, period: str = "monthly") -> Dict:
        """
        Check current token usage against budget.
        
        Args:
            project_id: Project UUID
            period: "monthly" or "daily"
            
        Returns:
            {
                "used": 45000,
                "limit": 100000,
                "remaining": 55000,
                "percentage": 45.0,
                "status": "ok" | "warning" | "exceeded",
                "period": "monthly",
                "period_start": "2024-01-01T00:00:00Z"
            }
        """
        # Determine time range
        if period == "monthly":
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            limit = self.budget_limits.get(project_id, float('inf'))
        else:  # daily
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            limit = self.daily_limits.get(project_id, float('inf'))
        
        # Query token usage
        try:
            result = self.client.rpc('get_token_usage', {
                'p_project_id': project_id,
                'p_start_date': start_date.isoformat()
            }).execute()
            
            used = result.data[0]['total_tokens'] if result.data and result.data[0]['total_tokens'] else 0
        except Exception as e:
            print(f"Error fetching token usage: {e}")
            used = 0
        
        # Calculate metrics
        remaining = max(0, limit - used) if limit != float('inf') else float('inf')
        percentage = (used / limit * 100) if limit > 0 and limit != float('inf') else 0
        
        # Determine status
        status = "ok"
        if percentage >= 100:
            status = "exceeded"
        elif percentage >= 80:
            status = "warning"
            
        return {
            "used": used,
            "limit": limit if limit != float('inf') else None,
            "remaining": remaining if remaining != float('inf') else None,
            "percentage": round(percentage, 2),
            "status": status,
            "period": period,
            "period_start": start_date.isoformat()
        }
        
    async def get_cost_breakdown(self, project_id: str, days: int = 30) -> Dict:
        """
        Get detailed cost breakdown by workflow and model.
        
        Args:
            project_id: Project UUID
            days: Number of days to analyze (default: 30)
            
        Returns:
            {
                "total_cost": 12.45,
                "total_tokens": 500000,
                "by_workflow": [...],
                "by_model": {...}
            }
        """
        try:
            result = self.client.rpc('get_cost_breakdown', {
                'p_project_id': project_id,
                'p_days': days
            }).execute()
            
            workflows = result.data if result.data else []
            
            # Calculate totals
            total_cost = sum(float(w.get('cost', 0) or 0) for w in workflows)
            total_tokens = sum(int(w.get('total_tokens', 0) or 0) for w in workflows)
            
            # Group by model
            by_model = {}
            for w in workflows:
                model = w.get('model', 'unknown')
                if model not in by_model:
                    by_model[model] = {
                        'tokens': 0,
                        'cost': 0,
                        'calls': 0
                    }
                by_model[model]['tokens'] += int(w.get('total_tokens', 0) or 0)
                by_model[model]['cost'] += float(w.get('cost', 0) or 0)
                by_model[model]['calls'] += int(w.get('call_count', 0) or 0)
            
            return {
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "by_workflow": workflows,
                "by_model": by_model,
                "period_days": days
            }
        except Exception as e:
            print(f"Error fetching cost breakdown: {e}")
            return {
                "total_cost": 0,
                "total_tokens": 0,
                "by_workflow": [],
                "by_model": {},
                "period_days": days,
                "error": str(e)
            }
    
    async def get_usage_trend(self, project_id: str, days: int = 7) -> List[Dict]:
        """
        Get daily token usage trend.
        
        Args:
            project_id: Project UUID
            days: Number of days to retrieve
            
        Returns:
            [
                {"date": "2024-01-15", "tokens": 12000, "cost": 0.24},
                {"date": "2024-01-16", "tokens": 15000, "cost": 0.30},
                ...
            ]
        """
        try:
            result = self.client.rpc('get_usage_trend', {
                'p_project_id': project_id,
                'p_days': days
            }).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching usage trend: {e}")
            return []
    
    async def get_top_expensive_executions(self, project_id: str, limit: int = 10) -> List[Dict]:
        """
        Get the most expensive workflow executions.
        
        Args:
            project_id: Project UUID
            limit: Number of results to return
            
        Returns:
            [
                {
                    "execution_id": "uuid",
                    "workflow_name": "ChatWorkflow",
                    "tokens": 5000,
                    "cost": 0.10,
                    "started_at": "2024-01-15T10:30:00Z"
                },
                ...
            ]
        """
        try:
            # Query executions with token usage
            result = self.client.rpc('get_top_expensive_executions', {
                'p_project_id': project_id,
                'p_limit': limit
            }).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching expensive executions: {e}")
            return []


class BudgetAlertSystem:
    """
    Alert system for token budget monitoring.
    
    Features:
    - Customizable alert handlers (email, Slack, webhooks)
    - Automatic budget checking
    - Alert throttling to prevent spam
    """
    
    def __init__(self, token_monitor: TokenMonitor):
        """
        Initialize alert system.
        
        Args:
            token_monitor: TokenMonitor instance
        """
        self.monitor = token_monitor
        self.alert_handlers: List[Callable] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self.alert_cooldown_minutes = 60  # Don't spam alerts
        
    def add_alert_handler(self, handler: Callable):
        """
        Add a custom alert handler.
        
        Args:
            handler: Async function(project_id, alert_type, message, data)
            
        Example:
            async def email_alert(project_id, alert_type, message, data):
                send_email(to="admin@example.com", subject=alert_type, body=message)
            
            alerts.add_alert_handler(email_alert)
        """
        self.alert_handlers.append(handler)
        
    async def check_and_alert(self, project_id: str):
        """
        Check budget and trigger alerts if needed.
        
        Args:
            project_id: Project UUID
        """
        # Check both monthly and daily budgets
        for period in ["monthly", "daily"]:
            status = await self.monitor.check_budget(project_id, period=period)
            
            alert_key = f"{project_id}:{period}:{status['status']}"
            
            # Check if we should send alert (cooldown)
            if alert_key in self.last_alert_times:
                time_since_last = datetime.now() - self.last_alert_times[alert_key]
                if time_since_last.total_seconds() < self.alert_cooldown_minutes * 60:
                    continue  # Skip, too soon
            
            # Trigger alerts based on status
            if status['status'] == 'exceeded':
                await self._trigger_alerts(
                    project_id,
                    "BUDGET_EXCEEDED",
                    f"{period.capitalize()} token budget exceeded: {status['used']:,}/{status['limit']:,}  tokens",
                    status
                )
                self.last_alert_times[alert_key] = datetime.now()
                
            elif status['status'] == 'warning':
                await self._trigger_alerts(
                    project_id,
                    "BUDGET_WARNING",
                    f"{period.capitalize()} token budget at {status['percentage']}%",
                    status
                )
                self.last_alert_times[alert_key] = datetime.now()
                
    async def _trigger_alerts(self, project_id: str, alert_type: str, message: str, data: Dict):
        """
        Trigger all registered alert handlers.
        
        Args:
            project_id: Project UUID
            alert_type: Type of alert
            message: Alert message
            data: Additional data
        """
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(project_id, alert_type, message, data)
                else:
                    handler(project_id, alert_type, message, data)
            except Exception as e:
                print(f"Alert handler failed: {e}")
    
    async def monitor_continuously(self, project_ids: List[str], check_interval_minutes: int = 15):
        """
        Continuously monitor projects and send alerts.
        
        Args:
            project_ids: List of project UUIDs to monitor
            check_interval_minutes: How often to check (default: 15 minutes)
        """
        print(f"🔍 Starting continuous monitoring for {len(project_ids)} projects")
        print(f"   Check interval: {check_interval_minutes} minutes")
        
        while True:
            for project_id in project_ids:
                try:
                    await self.check_and_alert(project_id)
                except Exception as e:
                    print(f"Error monitoring project {project_id}: {e}")
            
            await asyncio.sleep(check_interval_minutes * 60)


# Example alert handlers

async def console_alert(project_id: str, alert_type: str, message: str, data: Dict):
    """Simple console alert handler."""
    print(f"\n{'='*60}")
    print(f"🚨 ALERT: {alert_type}")
    print(f"Project: {project_id}")
    print(f"Message: {message}")
    print(f"Data: {data}")
    print(f"{'='*60}\n")


async def email_alert(project_id: str, alert_type: str, message: str, data: Dict):
    """
    Email alert handler (requires email service setup).
    
    Example using SendGrid:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        email = Mail(
            from_email='alerts@agora.com',
            to_emails='admin@example.com',
            subject=f'Agora Alert: {alert_type}',
            html_content=f'<p>{message}</p><pre>{data}</pre>'
        )
        sg.send(email)
    """
    print(f"📧 Email alert: {message}")
    # TODO: Implement actual email sending


async def slack_alert(project_id: str, alert_type: str, message: str, data: Dict):
    """
    Slack alert handler (requires Slack webhook).
    
    Example:
        import httpx
        
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={
                'text': f'🚨 {alert_type}: {message}',
                'attachments': [{
                    'color': 'danger' if 'EXCEEDED' in alert_type else 'warning',
                    'fields': [
                        {'title': 'Project', 'value': project_id, 'short': True},
                        {'title': 'Usage', 'value': f"{data['used']:,} tokens", 'short': True},
                        {'title': 'Limit', 'value': f"{data['limit']:,} tokens", 'short': True},
                        {'title': 'Percentage', 'value': f"{data['percentage']}%", 'short': True}
                    ]
                }]
            })
    """
    print(f"💬 Slack alert: {message}")
    # TODO: Implement actual Slack webhook
