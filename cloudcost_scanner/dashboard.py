from dash import Dash, html, dcc, dash_table
import plotly.graph_objs as go
import json
import re

def clean_name(name):
    # Convert resource_name like "aws_db_subnet_group" → "DB Subnet"
    parts = re.sub(r'^aws_|_resource|_group|_instance|_bucket', '', name)
    parts = parts.replace('_', ' ').title()
    return parts.strip()

def launch_dashboard(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

    resources = data.get("resources", [])
    total_estimated = sum(r.get("estimated_cost", 0) for r in resources)
    total_actual = sum(r.get("actual_cost", 0) for r in resources)
    budget = data.get("budget", 100)

    # Summary metrics
    diff = total_estimated - budget
    status = "✅ Within Budget" if diff <= 0 else "🚨 Over Budget"
    color = "#10b981" if diff <= 0 else "#ef4444"
    diff_percent = (diff / budget * 100) if budget > 0 else 0

    # Shorten resource names for display
    for r in resources:
        r["display_name"] = clean_name(r.get("name", "Unknown"))

    # --- Enhanced Bar Chart ---
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["display_name"] for r in resources],
        y=[r["estimated_cost"] for r in resources],
        name="Estimated Cost",
        marker_color="#3b82f6",
        marker_line_color="#2563eb",
        marker_line_width=1.5,
        hovertemplate='<b>%{x}</b><br>Estimated: $%{y:.2f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=[r["display_name"] for r in resources],
        y=[r["actual_cost"] for r in resources],
        name="Actual Cost",
        marker_color="#f59e0b",
        marker_line_color="#d97706",
        marker_line_width=1.5,
        hovertemplate='<b>%{x}</b><br>Actual: $%{y:.2f}<extra></extra>'
    ))
    fig.update_layout(
        barmode='group',
        title={
            'text': "Cost Analysis by Resource",
            'font': {'size': 20, 'color': '#1f2937', 'family': 'Arial, sans-serif'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Resource",
        yaxis_title="Cost ($)",
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#ffffff",
        font=dict(size=13, color='#374151', family='Arial, sans-serif'),
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(gridcolor='#e5e7eb', showline=True, linecolor='#d1d5db'),
        yaxis=dict(gridcolor='#e5e7eb', showline=True, linecolor='#d1d5db'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#d1d5db",
            borderwidth=1
        ),
        hovermode='x unified'
    )

    # --- Enhanced Table ---
    table = dash_table.DataTable(
        columns=[
            {"name": "Resource", "id": "display_name"},
            {"name": "Estimated ($)", "id": "estimated_cost"},
            {"name": "Actual ($)", "id": "actual_cost"},
            {"name": "Status", "id": "status"},
        ],
        data=[
            {
                "display_name": r["display_name"],
                "estimated_cost": f"${r['estimated_cost']:.2f}",
                "actual_cost": f"${r['actual_cost']:.2f}",
                "status": "✅ OK" if r["estimated_cost"] <= budget else "🚨 Exceeded",
            }
            for r in resources
        ],
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #e5e7eb',
            'borderRadius': '8px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '12px',
            'fontSize': 14,
            'fontFamily': 'Arial, sans-serif',
            'color': '#374151'
        },
        style_header={
            'backgroundColor': '#f3f4f6',
            'fontWeight': 'bold',
            'color': '#1f2937',
            'borderBottom': '2px solid #d1d5db'
        },
        style_data={
            'borderBottom': '1px solid #e5e7eb'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{status} contains "🚨"'},
                'backgroundColor': '#fef2f2',
                'color': '#991b1b'
            },
            {
                'if': {'filter_query': '{status} contains "✅"'},
                'backgroundColor': '#f0fdf4',
                'color': '#166534'
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#fafafa'
            }
        ],
    )

    app = Dash(__name__)
    app.title = "Cloud Cost Overview"

    app.layout = html.Div(
        style={
            'fontFamily': 'Arial, sans-serif',
            'padding': '40px',
            'backgroundColor': '#f9fafb',
            'minHeight': '100vh'
        },
        children=[
            # Header
            html.Div([
                html.H1(
                    "☁️ Cloud Cost Dashboard",
                    style={
                        'textAlign': 'center',
                        'color': '#1f2937',
                        'marginBottom': '10px',
                        'fontSize': '32px',
                        'fontWeight': '700'
                    }
                ),
                html.P(
                    "Monitor and analyze your cloud infrastructure costs",
                    style={
                        'textAlign': 'center',
                        'color': '#6b7280',
                        'marginBottom': '30px',
                        'fontSize': '16px'
                    }
                )
            ]),
            
            # Metrics Cards
            html.Div([
                # Estimated Cost Card
                html.Div([
                    html.Div("💰", style={'fontSize': '32px', 'marginBottom': '8px'}),
                    html.Div("Estimated Cost", style={'color': '#6b7280', 'fontSize': '14px', 'marginBottom': '4px'}),
                    html.Div(f"${total_estimated:.2f}", style={'fontSize': '28px', 'fontWeight': '700', 'color': '#1f2937'})
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
                    'flex': '1',
                    'textAlign': 'center',
                    'border': '1px solid #e5e7eb'
                }),
                
                # Budget Card
                html.Div([
                    html.Div("🎯", style={'fontSize': '32px', 'marginBottom': '8px'}),
                    html.Div("Budget", style={'color': '#6b7280', 'fontSize': '14px', 'marginBottom': '4px'}),
                    html.Div(f"${budget:.2f}", style={'fontSize': '28px', 'fontWeight': '700', 'color': '#1f2937'})
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
                    'flex': '1',
                    'textAlign': 'center',
                    'border': '1px solid #e5e7eb'
                }),
                
                # Status Card
                html.Div([
                    html.Div("📊", style={'fontSize': '32px', 'marginBottom': '8px'}),
                    html.Div("Status", style={'color': '#6b7280', 'fontSize': '14px', 'marginBottom': '4px'}),
                    html.Div(
                        status,
                        style={
                            'fontSize': '20px',
                            'fontWeight': '700',
                            'color': color
                        }
                    ),
                    html.Div(
                        f"{'+' if diff > 0 else ''}{diff_percent:.1f}%",
                        style={
                            'fontSize': '16px',
                            'color': color,
                            'marginTop': '4px'
                        }
                    )
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
                    'flex': '1',
                    'textAlign': 'center',
                    'border': '1px solid #e5e7eb'
                }),
            ], style={
                'display': 'flex',
                'gap': '20px',
                'marginBottom': '30px',
                'flexWrap': 'wrap'
            }),
            
            # Chart Container
            html.Div([
                dcc.Graph(figure=fig, style={'height': '500px'})
            ], style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '12px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
                'marginBottom': '30px',
                'border': '1px solid #e5e7eb'
            }),
            
            # Table Container
            html.Div([
                html.H3(
                    "Resource Cost Breakdown",
                    style={
                        'color': '#1f2937',
                        'marginBottom': '20px',
                        'fontSize': '20px',
                        'fontWeight': '600'
                    }
                ),
                table
            ], style={
                'backgroundColor': '#ffffff',
                'padding': '24px',
                'borderRadius': '12px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
                'border': '1px solid #e5e7eb'
            })
        ]
    )

    print(f"\n🔗 Dashboard available at: http://127.0.0.1:8050\n")
    app.run(debug=False)


# Example call:
# launch_dashboard("output.json")