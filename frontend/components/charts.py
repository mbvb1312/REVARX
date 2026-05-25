import plotly.graph_objects as go

COLOR_A = "#2563EB"
COLOR_B = "#F97316"
COLOR_GOOD = "#16A34A"
COLOR_WARN = "#CA8A04"
COLOR_BAD = "#DC2626"
COLOR_MUTED = "#64748B"
TEXT_COLOR = "#172033"
GRID_COLOR = "rgba(100, 116, 139, 0.18)"


def _layout(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=35, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def funnel_chart(sent: int, replied: int, recovered: int) -> go.Figure:
    fig = go.Figure(
        go.Funnel(
            y=["Recovery emails sent", "Replies received", "Customers re-engaged"],
            x=[sent, replied, recovered],
            textinfo="value+percent initial",
            marker=dict(color=[COLOR_A, COLOR_WARN, COLOR_GOOD]),
            connector=dict(fillcolor="rgba(148, 163, 184, 0.2)"),
        )
    )
    return _layout(fig, 320)


def ab_bar_chart(a_rate: float, b_rate: float) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                name="A: Professional",
                x=["Conversion rate"],
                y=[a_rate],
                marker_color=COLOR_A,
                text=[f"{a_rate}%"],
                textposition="auto",
            ),
            go.Bar(
                name="B: Friendly",
                x=["Conversion rate"],
                y=[b_rate],
                marker_color=COLOR_B,
                text=[f"{b_rate}%"],
                textposition="auto",
            ),
        ]
    )
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Hot/warm conversion (%)")
    return _layout(fig, 320)


def hourly_heatmap(hourly_data: list) -> go.Figure:
    hours = [f"{row['hour']}:00" for row in hourly_data]
    counts = [row["count"] for row in hourly_data]
    fig = go.Figure(
        data=[
            go.Bar(
                x=hours,
                y=counts,
                marker=dict(color=counts, colorscale=[[0, COLOR_MUTED], [0.5, COLOR_WARN], [1, COLOR_GOOD]], showscale=False),
                text=counts,
                textposition="outside",
            )
        ]
    )
    fig.update_xaxes(title="Hour")
    fig.update_yaxes(title="Replies")
    return _layout(fig, 320)


def tone_performance_chart(tone_data: dict) -> go.Figure:
    labels = []
    values = []
    for tone in ["professional", "friendly"]:
        labels.append(tone.title())
        values.append(tone_data.get(tone, 0))

    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color=[COLOR_A, COLOR_B],
                text=[f"{value}%" for value in values],
                textposition="auto",
            )
        ]
    )
    fig.update_xaxes(title="Hot/warm conversion (%)")
    return _layout(fig, 300)


def demographic_ab_chart(rows: list, title: str = "") -> go.Figure:
    rows = rows or []
    segments = [str(row.get("segment", "Unknown")) for row in rows]
    a_rates = [row.get("variant_a_rate", 0) for row in rows]
    b_rates = [row.get("variant_b_rate", 0) for row in rows]

    fig = go.Figure(
        data=[
            go.Bar(name="A: Professional", x=segments, y=a_rates, marker_color=COLOR_A, text=[f"{v}%" for v in a_rates]),
            go.Bar(name="B: Friendly", x=segments, y=b_rates, marker_color=COLOR_B, text=[f"{v}%" for v in b_rates]),
        ]
    )
    fig.update_layout(title=title, barmode="group")
    fig.update_yaxes(title="Conversion (%)")
    return _layout(fig, 360)


def status_donut(status_counts: dict) -> go.Figure:
    labels = ["Pending", "Hot", "Warm", "Cold", "No response", "Email failed", "Unsubscribed", "New"]
    keys = ["pending", "hot", "warm", "cold", "no_response", "email_failed", "unsubscribed", "new"]
    values = [status_counts.get(key, 0) for key in keys]
    colors = [COLOR_WARN, COLOR_GOOD, "#84CC16", COLOR_A, COLOR_MUTED, COLOR_BAD, "#991B1B", "#14B8A6"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors),
                textinfo="label+value",
            )
        ]
    )
    return _layout(fig, 320)
