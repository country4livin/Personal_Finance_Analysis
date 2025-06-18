import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Load and preprocess data
df = pd.read_csv("Resources/Personal_Finance_Dataset.csv", parse_dates=["Date"])
df["Month"] = df["Date"].dt.to_period("M")

# Categorize spending types
needs = ["Rent", "Utilities", "Health & Fitness", "Food & Drink"]
wants = ["Entertainment", "Shopping", "Travel"]

def categorize(row):
    if row["Type"] == "Income":
        return "Income"
    elif row["Category"] in needs:
        return "Needs"
    elif row["Category"] in wants:
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

# Layout
app.layout = html.Div([
    html.H1("📊 Personal Budget Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Label("Monthly Income:"),
        dcc.Input(id="user-income", type="number", value=5000, step=100),

        html.Label("Needs %:"),
        dcc.Input(id="needs-percent", type="number", value=50),

        html.Label("Wants %:"),
        dcc.Input(id="wants-percent", type="number", value=30),

        html.Label("Savings %:"),
        dcc.Input(id="savings-percent", type="number", value=20),
    ], style={"padding": "10px", "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "10px"}),

    dcc.Graph(id="budget-graph"),

    dcc.Slider(
        min=0, max=len(summary) - 1, step=1,
        marks={i: str(summary['Month'].iloc[i]) for i in range(0, len(summary), 3)},
        value=len(summary) - 1,
        id="month-slider"
    )
])

@app.callback(
    Output("budget-graph", "figure"),
    [
        Input("month-slider", "value"),
        Input("user-income", "value"),
        Input("needs-percent", "value"),
        Input("wants-percent", "value"),
        Input("savings-percent", "value")
    ]
)
def update_chart(month_index, user_income, needs_pct, wants_pct, savings_pct):
    row = summary.iloc[month_index]
    month = row["Month"]
    needs = row.get("Needs", 0)
    wants = row.get("Wants", 0)
    savings = row.get("Savings", 0)

    fig = go.Figure()

    # Needs
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=needs,
        domain={"x": [0, 0.3], "y": [0.7, 1]},
        title={"text": f"Needs (Max {needs_pct}%)"},
        gauge={"axis": {"range": [0, user_income * needs_pct / 100]},
               "bar": {"color": "green" if needs <= user_income * needs_pct / 100 else "red"}}
    ))

    # Wants
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=wants,
        domain={"x": [0.35, 0.65], "y": [0.7, 1]},
        title={"text": f"Wants (Max {wants_pct}%)"},
        gauge={"axis": {"range": [0, user_income * wants_pct / 100]},
               "bar": {"color": "green" if wants <= user_income * wants_pct / 100 else "red"}}
    ))

    # Savings
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=savings,
        domain={"x": [0.7, 1], "y": [0.7, 1]},
        title={"text": f"Savings (Goal {savings_pct}%)"},
        gauge={"axis": {"range": [0, user_income * savings_pct / 100]},
               "bar": {"color": "green" if savings >= user_income * savings_pct / 100 else "red"}}
    ))

    fig.update_layout(
        height=450,
        title_text=f"Budget Snapshot for {month}",
        margin={"t": 60, "b": 30}
    )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)