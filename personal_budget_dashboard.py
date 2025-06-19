import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Load and preprocess dataset
df = pd.read_csv("Resources/Personal_Finance_Dataset.csv", parse_dates=["Date"])
df["Month"] = df["Date"].dt.to_period("M")

# Define budgeting categories
needs_categories = ["Rent", "Utilities", "Health & Fitness", "Food & Drink"]
wants_categories = ["Entertainment", "Shopping", "Travel"]

def categorize(row):
    if row["Type"] == "Income":
        return "Income"
    elif row["Category"] in needs_categories:
        return "Needs"
    elif row["Category"] in wants_categories:
        return "Wants"
    else:
        return "Other"

df["SpendingType"] = df.apply(categorize, axis=1)

# Monthly summary
summary = df.groupby(["Month", "SpendingType"])["Amount"].sum().unstack().fillna(0)
summary["Total Expenses"] = summary["Needs"] + summary["Wants"]
summary["Savings"] = summary["Income"] - summary["Total Expenses"]
summary = summary.reset_index()

# Initialize Dash app
app = Dash(__name__)
app.title = "Personal Budget Dashboard"

app.layout = html.Div([
    html.H1("📊 Personal Budget Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.H2("💼 Customize Your Monthly Budget"),
        html.Div([
            html.Div([
                html.Label("Monthly Income"),
                dcc.Input(id="user-income", type="number", value=5000, step=100)
            ]),
            html.Div([
                html.Label("Needs %"),
                dcc.Input(id="needs-percent", type="number", value=50)
            ]),
            html.Div([
                html.Label("Wants %"),
                dcc.Input(id="wants-percent", type="number", value=30)
            ]),
            html.Div([
                html.Label("Savings %"),
                dcc.Input(id="savings-percent", type="number", value=20)
            ])
        ], style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "20px",
            "marginBottom": "30px"
        }),
    ], style={"marginBottom": "30px"}),

    html.Hr(),

    html.H3("📈 Budget Breakdown (Gauge View)"),
    dcc.Graph(id="budget-graph"),

html.Div([
    html.Label("Select Month:"),
    dcc.Slider(
        min=0, max=len(summary) - 1, step=1,
        marks={i: str(summary["Month"].iloc[i]) for i in range(0, len(summary), 6)},
        value=len(summary) - 1,
        id="month-slider",
        tooltip={"placement": "bottom", "always_visible": False}
    )
], style={"margin": "40px 0"}),

    html.H3("📊 Spending Trends (Line Chart)"),
    dcc.Graph(id="trend-line"),

], style={"padding": "30px", "maxWidth": "1000px", "margin": "auto"})

@app.callback(
    [Output("budget-graph", "figure"),
     Output("trend-line", "figure")],
    [Input("month-slider", "value"),
     Input("user-income", "value"),
     Input("needs-percent", "value"),
     Input("wants-percent", "value"),
     Input("savings-percent", "value")]
)
def update_chart(month_index, user_income, needs_pct, wants_pct, savings_pct):
    # Apply safe defaults
    user_income = user_income or 5000
    needs_pct = needs_pct or 50
    wants_pct = wants_pct or 30
    savings_pct = savings_pct or 20

    try:
        income = float(user_income)
        needs_limit = income * float(needs_pct) / 100
        wants_limit = income * float(wants_pct) / 100
        savings_goal = income * float(savings_pct) / 100
    except (ValueError, TypeError):
        income, needs_limit, wants_limit, savings_goal = 5000, 2500, 1500, 1000

    row = summary.iloc[month_index]
    needs_spent = row.get("Needs", 0)
    wants_spent = row.get("Wants", 0)
    savings = row.get("Savings", 0)
    month = row["Month"]

    # Gauge chart
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=needs_spent,
        domain={"x": [0, 0.3], "y": [0.5, 0.9]},
        title={"text": "Needs"},
        gauge={
            "axis": {"range": [0, needs_limit]},
            "bar": {"color": "red" if needs_spent > needs_limit else "green"}
        }
    ))

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=wants_spent,
        domain={"x": [0.35, 0.65], "y": [0.5, 0.9]},
        title={"text": "Wants"},
        gauge={
            "axis": {"range": [0, wants_limit]},
            "bar": {"color": "red" if wants_spent > wants_limit else "green"}
        }
    ))

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=max(0, savings),
        domain={"x": [0.7, 1], "y": [0.5, 0.9]},
        title={"text": f"Savings: ${savings:,.0f}"},
        gauge={
            "axis": {"range": [0, savings_goal]},
            "bar": {"color": "green" if savings >= savings_goal else "red"}
        }
    ))

    fig.update_layout(
        height=500,
        title_text=f"Budget Snapshot for {month}",
        margin={"t": 60, "b": 40}
    )

    # Trend line chart
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=summary["Month"].astype(str),
        y=summary["Needs"],
        mode="lines+markers",
        name="Needs",
        line=dict(color="red")
    ))
    trend_fig.add_trace(go.Scatter(
        x=summary["Month"].astype(str),
        y=summary["Wants"],
        mode="lines+markers",
        name="Wants",
        line=dict(color="orange")
    ))
    trend_fig.add_trace(go.Scatter(
        x=summary["Month"].astype(str),
        y=summary["Savings"],
        mode="lines+markers",
        name="Savings",
        line=dict(color="green")
    ))

    trend_fig.update_layout(
        title="Month-over-Month Spending Trends",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        height=400,
        margin={"t": 50, "b": 40}
    )

    return fig, trend_fig

if __name__ == "__main__":
    app.run(debug=True)