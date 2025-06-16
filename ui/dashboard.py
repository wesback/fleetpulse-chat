"""Fleet dashboard integration for Streamlit UI."""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from core.mcp_client import FleetPulseMCPClient


class FleetDashboard:
    """Fleet dashboard for visualizing FleetPulse data."""
    
    def __init__(self):
        self.mcp_client = FleetPulseMCPClient()
    
    async def render_overview_dashboard(self):
        """Render the main fleet overview dashboard."""
        st.header("🚀 Fleet Overview Dashboard")
          # Get fleet status
        fleet_result = await self.mcp_client.execute_tool("list_hosts", {})
        
        if fleet_result.success:
            fleet_data = fleet_result.data
            self._render_fleet_metrics(fleet_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                await self._render_host_status_chart(fleet_data)
            
            with col2:
                await self._render_update_status_chart()
        else:
            st.error(f"Failed to load fleet data: {fleet_result.error}")
    
    def _render_fleet_metrics(self, fleet_data: Dict[str, Any]):
        """Render key fleet metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_hosts = fleet_data.get("total_hosts", 0)
            st.metric("Total Hosts", total_hosts)
        
        with col2:
            online_hosts = fleet_data.get("online_hosts", 0)
            offline_hosts = total_hosts - online_hosts
            st.metric("Online Hosts", online_hosts, delta=f"-{offline_hosts} offline")
        
        with col3:
            pending_updates = fleet_data.get("total_pending_updates", 0)
            st.metric("Pending Updates", pending_updates)
        
        with col4:
            security_updates = fleet_data.get("security_updates", 0)
            delta_color = "inverse" if security_updates > 0 else "normal"
            st.metric("Security Updates", security_updates, delta_color=delta_color)
    
    async def _render_host_status_chart(self, fleet_data: Dict[str, Any]):
        """Render host status distribution chart."""
        st.subheader("Host Status Distribution")
        
        # Create pie chart data
        labels = ["Online", "Offline", "Maintenance"]
        values = [
            fleet_data.get("online_hosts", 0),
            fleet_data.get("offline_hosts", 0),
            fleet_data.get("maintenance_hosts", 0)
        ]
        
        colors = ["#00cc96", "#ff6692", "#ffa15a"]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors
        )])
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    async def _render_update_status_chart(self):
        """Render update status across the fleet."""
        st.subheader("Update Status")
          # Get recent update reports
        updates_result = await self.mcp_client.execute_tool("get_update_reports", {"days": 7})
        
        if updates_result.success:
            updates_data = updates_result.data.get("hosts", [])
            
            # Process data for chart
            severity_counts = {"critical": 0, "important": 0, "moderate": 0, "low": 0}
            
            for host in updates_data:
                for update in host.get("pending_updates", []):
                    severity = update.get("severity", "low").lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
            
            # Create bar chart
            df = pd.DataFrame([
                {"Severity": k.capitalize(), "Count": v}
                for k, v in severity_counts.items()
            ])
            
            if not df.empty:
                fig = px.bar(
                    df,
                    x="Severity",
                    y="Count",
                    color="Severity",
                    color_discrete_map={
                        "Critical": "#ff4b4b",
                        "Important": "#ff8c00",
                        "Moderate": "#ffd700",
                        "Low": "#00cc96"
                    }
                )
                
                fig.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No pending updates")
        else:
            st.error("Failed to load update data")
    
    async def render_host_details_dashboard(self, hostname: str):
        """Render detailed dashboard for a specific host."""
        st.header(f"🖥️ Host Dashboard: {hostname}")
        
        # Get host details
        host_result = await self.mcp_client.execute_tool("get_host_details", {"hostname": hostname})
        
        if not host_result.success:
            st.error(f"Failed to load host data: {host_result.error}")
            return
        
        host_data = host_result.data
        
        # Host information
        self._render_host_info(host_data)
        
        # System metrics
        await self._render_system_metrics(hostname)
        
        # Update history
        await self._render_update_history_chart(hostname)
        
        # Package information
        await self._render_package_status(hostname)
    
    def _render_host_info(self, host_data: Dict[str, Any]):
        """Render basic host information."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("OS Distribution", host_data.get("os_name", "Unknown"))
            st.metric("Kernel Version", host_data.get("kernel_version", "Unknown"))
        
        with col2:
            uptime = host_data.get("uptime", "Unknown")
            st.metric("Uptime", uptime)
            
            last_seen = host_data.get("last_seen", "Unknown")
            st.metric("Last Seen", last_seen)
        
        with col3:
            cpu_cores = host_data.get("cpu_cores", 0)
            st.metric("CPU Cores", cpu_cores)
            
            memory_gb = host_data.get("memory_gb", 0)
            st.metric("Memory (GB)", memory_gb)
    
    async def _render_system_metrics(self, hostname: str):
        """Render system performance metrics."""
        st.subheader("📊 System Metrics")
        
        metrics_result = await self.mcp_client.execute_tool(
            "get_host_details",
            {"hostname": hostname}
        )
        
        if metrics_result.success:
            metrics_data = metrics_result.data
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cpu_usage = metrics_data.get("cpu_usage", 0)
                st.metric("CPU Usage", f"{cpu_usage}%")
                st.progress(cpu_usage / 100)
            
            with col2:
                memory_usage = metrics_data.get("memory_usage", 0)
                st.metric("Memory Usage", f"{memory_usage}%")
                st.progress(memory_usage / 100)
            
            with col3:
                disk_usage = metrics_data.get("disk_usage", 0)
                st.metric("Disk Usage", f"{disk_usage}%")
                st.progress(disk_usage / 100)
        else:
            st.warning("System metrics not available")
    
    async def _render_update_history_chart(self, hostname: str):
        """Render update history timeline chart."""
        st.subheader("📜 Update History")
        
        history_result = await self.mcp_client.execute_tool(
            "get_update_history",
            {"hostname": hostname, "days": 90}
        )
        
        if history_result.success:
            history_data = history_result.data.get("updates", [])
            
            if history_data:
                # Process data for timeline chart
                df_data = []
                for update in history_data:
                    date = datetime.fromisoformat(update.get("date", ""))
                    packages_count = len(update.get("packages", []))
                    df_data.append({
                        "Date": date,
                        "Packages Updated": packages_count
                    })
                
                df = pd.DataFrame(df_data)
                
                fig = px.line(
                    df,
                    x="Date",
                    y="Packages Updated",
                    title="Package Updates Over Time"
                )
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No update history available")
        else:
            st.warning("Update history not available")
    
    async def _render_package_status(self, hostname: str):
        """Render package status information."""
        st.subheader("📦 Package Status")
          # Get recent updates for this host
        updates_result = await self.mcp_client.execute_tool("get_host_reports", {"hostname": hostname, "days": 30})
        
        if updates_result.success:
            all_hosts = updates_result.data.get("hosts", [])
            host_data = next((h for h in all_hosts if h.get("hostname") == hostname), None)
            
            if host_data:
                pending_updates = host_data.get("pending_updates", [])
                
                if pending_updates:
                    # Group by severity
                    severity_groups = {}
                    for update in pending_updates:
                        severity = update.get("severity", "low")
                        if severity not in severity_groups:
                            severity_groups[severity] = []
                        severity_groups[severity].append(update)
                    
                    # Display by severity
                    for severity in ["critical", "important", "moderate", "low"]:
                        if severity in severity_groups:
                            with st.expander(f"{severity.capitalize()} Updates ({len(severity_groups[severity])})"):
                                for update in severity_groups[severity]:
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    
                                    with col1:
                                        st.write(f"**{update.get('package_name', 'Unknown')}**")
                                        st.caption(update.get("description", "No description"))
                                    
                                    with col2:
                                        st.write(f"Current: {update.get('current_version', 'Unknown')}")
                                    
                                    with col3:
                                        st.write(f"Available: {update.get('available_version', 'Unknown')}")
                else:
                    st.success("All packages are up to date!")
            else:
                st.info("No package information available for this host")
        else:
            st.warning("Package status not available")
    
    async def render_fleet_reports_dashboard(self):
        """Render fleet reports and analytics dashboard."""
        st.header("📈 Fleet Reports & Analytics")
        
        # Report generation controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            report_format = st.selectbox("Report Format", ["json", "html", "pdf"])
        
        with col2:
            include_history = st.checkbox("Include History", value=True)
        
        with col3:
            if st.button("Generate Report", use_container_width=True):
                await self._generate_and_display_report(report_format, include_history)
        
        # Fleet trends
        await self._render_fleet_trends()
        
        # Compliance summary
        await self._render_compliance_summary()
    
    async def _generate_and_display_report(self, format: str, include_history: bool):
        """Generate and display fleet report."""
        with st.spinner("Generating report..."):
            report_result = await self.mcp_client.execute_tool(
                "get_fleet_statistics",
                {}
            )
            if report_result.success:
                report_data = report_result.data
                
                if format == "json":
                    st.json(report_data)
                elif format == "html":
                    st.markdown(str(report_data), unsafe_allow_html=True)
                else:
                    st.success("Report generated successfully!")
                    st.download_button(
                        "Download Report",
                        data=str(report_data),
                        file_name=f"fleet_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                    )
            else:
                st.error(f"Failed to generate report: {report_result.error}")
    
    async def _render_fleet_trends(self):
        """Render fleet trends over time."""
        st.subheader("📊 Fleet Trends")
        
        # Mock data for demonstration (replace with actual API calls)
        dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
        trend_data = pd.DataFrame({
            "Date": dates,
            "Total Hosts": [50 + i for i in range(len(dates))],
            "Up-to-date Hosts": [45 + (i % 10) for i in range(len(dates))],
            "Pending Updates": [20 - (i % 15) for i in range(len(dates))]
        })
        
        fig = px.line(
            trend_data,
            x="Date",
            y=["Total Hosts", "Up-to-date Hosts", "Pending Updates"],
            title="Fleet Trends Over Time"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    async def _render_compliance_summary(self):
        """Render compliance and security summary."""
        st.subheader("🔒 Compliance Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Security Patch Compliance", "85%", delta="5%")
            st.metric("Systems with Critical Updates", "3", delta="-2")
        
        with col2:
            st.metric("Average Patch Age", "12 days", delta="2 days")
            st.metric("Last Security Scan", "2 hours ago")


# Utility function to run async dashboard functions
def run_dashboard_async(dashboard_func, *args):
    """Run async dashboard function in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(dashboard_func(*args))