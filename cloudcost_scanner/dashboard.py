# dashboard.py
from dash import Dash, html, dcc, dash_table, Output, Input, callback
import plotly.graph_objs as go
import json
import re
import os
import math
from datetime import datetime

# -----------------------
# Utility functions
# -----------------------
def clean_name(name: str) -> str:
    """Shorten and prettify Terraform resource names."""
    if not name:
        return "unknown"
    # Remove aws_ prefix and common suffix words
    s = re.sub(r'^aws_', '', name)
    s = re.sub(r'(_resource|_group|_instance|_bucket|_subnet|_security_group)', '', s)
    s = s.replace('_', ' ').strip()
    # If dotted module-style name (module.foo.aws_s3_bucket.this) pick last meaningful token(s)
    if '.' in s:
        parts = [p for p in s.split('.') if p and not p.startswith('module')]
        if parts:
            s = parts[-1]
    # Title-case small words but keep abbreviations uppercase
    s = ' '.join([w.upper() if len(w) <= 3 and w.isalpha() else w.title() for w in s.split()])
    return s

def read_json_safe(path):
    """Read JSON file safely and return dict."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        # return empty structure if missing or invalid
        return {"resources": [], "total_estimated": 0.0, "total_budget": 0.0}

def format_money(v):
    try:
        return f"${v:,.2f}"
    except:
        return "$0.00"

def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0

# -----------------------
# App and layout
# -----------------------
app = Dash(__name__)
app.title = "Cloud Cost Overview"

app.layout = html.Div(
    style={'fontFamily': 'Arial, sans-serif', 'padding': '28px', 'backgroundColor': '#f8fafc', 'minHeight': '100vh'},
    children=[
        html.Div([
            html.H1("☁️ Cloud Cost Dashboard", style={'textAlign': 'center', 'color': '#0f172a', 'marginBottom': '6px', 'fontSize': '30px'}),
            html.P("Live view of latest cost scan results (auto-refreshes).", style={'textAlign': 'center', 'color': '#64748b', 'marginTop': '0', 'marginBottom': '18px'}),
        ]),
        # Interval: update every 10 seconds (10000 ms)
        dcc.Interval(id="interval-refresh", interval=10000, n_intervals=0),

        # Top metrics (Estimated, Budget, Status)
        html.Div(id="metrics-row", style={'display': 'flex', 'gap': '18px', 'marginBottom': '18px', 'flexWrap': 'wrap'}),

        # Charts and table area
        html.Div([
            html.Div(dcc.Graph(id='cost-bar-chart', config={'displayModeBar': False}), style={'flex': '1', 'minWidth': '320px', 'marginBottom': '18px'}),
            html.Div([
                html.H3("Resource Cost Breakdown", style={'marginTop': '0', 'color': '#0f172a'}),
                dash_table.DataTable(
                    id='resource-table',
                    columns=[
                        {"name": "Resource", "id": "display_name"},
                        {"name": "Estimated ($)", "id": "estimated_cost"},
                        {"name": "Actual ($)", "id": "actual_cost"},
                        {"name": "Budget ($)", "id": "budget"},
                        {"name": "Status", "id": "status"}
                    ],
                    data=[],
                    style_table={'overflowX': 'auto', 'maxHeight': '480px', 'overflowY': 'auto'},
                    style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': 13},
                    style_header={'backgroundColor': '#f1f5f9', 'fontWeight': '600'},
                    style_data_conditional=[
                        {'if': {'filter_query': '{status} contains "Exceeded"'}, 'backgroundColor': '#fff1f2', 'color': '#991b1b'},
                        {'if': {'filter_query': '{status} contains "OK"'}, 'backgroundColor': '#f0fdf4', 'color': '#166534'},
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#fcfbfd'}
                    ]
                )
            ], style={'width': '420px', 'minWidth': '300px', 'marginLeft': '20px'})
        ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}),

        # Footer / helper
        html.Div(id='last-updated', style={'marginTop': '14px', 'color': '#94a3b8'}),
    ]
)

# -----------------------
# Callbacks
# -----------------------
@app.callback(
    Output('cost-bar-chart', 'figure'),
    Output('resource-table', 'data'),
    Output('metrics-row', 'children'),
    Output('last-updated', 'children'),
    Input('interval-refresh', 'n_intervals')
)
def refresh_dashboard(n):
    """Reload output.json and update visuals."""
    json_path = os.path.join(os.getcwd(), "output.json")
    data = read_json_safe(json_path)

    resources = data.get("resources", [])
    # Normalize and compute sums
    for r in resources:
        # fallback keys if older format used
        if 'actual_cost' not in r:
            r['actual_cost'] = r.get('estimated_cost', 0) * 0.95
        if 'budget' not in r:
            r['budget'] = data.get('total_budget', 0)

        r['display_name'] = clean_name(r.get('name', 'Unknown'))
        r['estimated_cost'] = safe_float(r.get('estimated_cost', 0))
        r['actual_cost'] = safe_float(r.get('actual_cost', 0))
        r['budget'] = safe_float(r.get('budget', 0))

    total_estimated = safe_float(data.get('total_estimated', sum(r['estimated_cost'] for r in resources)))
    total_budget = safe_float(data.get('total_budget', data.get('total_budget', 0)))

    diff = total_estimated - total_budget
    diff_percent = (diff / total_budget * 100) if total_budget > 0 else 0
    status_text = "✅ Within Budget" if diff <= 0 else "🚨 Over Budget"
    status_color = "#10b981" if diff <= 0 else "#ef4444"

    # Bar chart
    names = [r['display_name'] for r in resources]
    est_vals = [r['estimated_cost'] for r in resources]
    act_vals = [r['actual_cost'] for r in resources]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=est_vals, name='Estimated', marker_color='#2563eb', hovertemplate='%{x}<br>Est: $%{y:.2f}<extra></extra>'))
    fig.add_trace(go.Bar(x=names, y=act_vals, name='Actual', marker_color='#f59e0b', hovertemplate='%{x}<br>Act: $%{y:.2f}<extra></extra>'))
    fig.update_layout(
        barmode='group',
        title={'text': 'Cost by Resource', 'x': 0.5},
        xaxis_title='Resource',
        yaxis_title='Cost ($)',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#f8fafc',
        margin=dict(t=50, b=80, l=50, r=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    # Table data
    table_rows = []
    for r in resources:
        st = "OK" if r['estimated_cost'] <= r['budget'] else "Exceeded"
        table_rows.append({
            "display_name": r['display_name'],
            "estimated_cost": format_money(r['estimated_cost']),
            "actual_cost": format_money(r['actual_cost']),
            "budget": format_money(r['budget']),
            "status": st
        })

    # Metrics cards
    metrics = [
        html.Div([
            html.Div("💰", style={'fontSize': '24px'}),
            html.Div("Estimated Total", style={'color': '#64748b', 'fontSize': 12}),
            html.Div(format_money(total_estimated), style={'fontSize': 20, 'fontWeight': 700, 'color': '#0f172a'})
        ], style={'backgroundColor': '#ffffff', 'padding': '14px', 'borderRadius': '10px', 'flex': '1', 'minWidth': '160px', 'border': '1px solid #e6eef6'}),
        html.Div([
            html.Div("🎯", style={'fontSize': '24px'}),
            html.Div("Budget", style={'color': '#64748b', 'fontSize': 12}),
            html.Div(format_money(total_budget), style={'fontSize': 20, 'fontWeight': 700, 'color': '#0f172a'})
        ], style={'backgroundColor': '#ffffff', 'padding': '14px', 'borderRadius': '10px', 'flex': '1', 'minWidth': '160px', 'border': '1px solid #e6eef6'}),
        html.Div([
            html.Div("📊", style={'fontSize': '24px'}),
            html.Div("Status", style={'color': '#64748b', 'fontSize': 12}),
            html.Div(status_text, style={'fontSize': 16, 'fontWeight': 700, 'color': status_color}),
            html.Div(f"{'+' if diff > 0 else ''}{diff_percent:.1f}%", style={'fontSize': 13, 'color': status_color})
        ], style={'backgroundColor': '#ffffff', 'padding': '14px', 'borderRadius': '10px', 'flex': '1', 'minWidth': '160px', 'border': '1px solid #e6eef6'})
    ]

    # Last updated text
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_updated = f"Last loaded: {ts} (auto-refresh every 10s) — data source: output.json"

    return fig, table_rows, metrics, last_updated

# -----------------------
# Run server (only when executed directly)
# -----------------------
if __name__ == "__main__":
    # helpful message
    print("Starting dashboard (local). If you run this in CI, dashboard will be disabled in the scanner.")
    app.run_server(debug=False, port=8050)
