import plotly.graph_objects as go

def funnel_chart(sent: int, replied: int, hot: int) -> go.Figure:
    """
    Renders a stunning horizontal funnel chart.
    """
    fig = go.Figure(go.Funnel(
        y=["Outreach Sent", "Replies Received", "Hot Leads 🔥"],
        x=[sent, replied, hot],
        textinfo="value+percent initial",
        marker=dict(
            color=["#636EFA", "#EF553B", "#00CC96"],
            line=dict(width=1, color="#1E1E1E")
        ),
        connector=dict(fillcolor="rgba(100, 100, 100, 0.2)")
    ))
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=10, b=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, Inter, sans-serif", size=12, color="#E0E0E0")
    )
    return fig

def ab_bar_chart(a_rate: float, b_rate: float) -> go.Figure:
    """
    Renders Variant A vs Variant B reply rates.
    """
    fig = go.Figure(data=[
        go.Bar(
            name="Variant A (Direct)",
            x=["Reply Rate (%)"],
            y=[a_rate],
            marker_color="#636EFA",
            text=[f"{a_rate}%"],
            textposition="auto"
        ),
        go.Bar(
            name="Variant B (Contextual)",
            x=["Reply Rate (%)"],
            y=[b_rate],
            marker_color="#EF553B",
            text=[f"{b_rate}%"],
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        yaxis=dict(
            title="Conversion Rate (%)",
            gridcolor="rgba(255, 255, 255, 0.1)",
            zeroline=False
        ),
        barmode="group",
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, Inter, sans-serif", size=12, color="#E0E0E0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def hourly_heatmap(hourly_data: list) -> go.Figure:
    """
    Renders bar chart for hourly replies.
    """
    hours = [f"{h['hour']}:00" for h in hourly_data]
    counts = [h["count"] for h in hourly_data]
    
    fig = go.Figure(data=[
        go.Bar(
            x=hours,
            y=counts,
            marker=dict(
                color=counts,
                colorscale="Viridis",
                showscale=False
            ),
            text=counts,
            textposition="outside"
        )
    ])
    
    fig.update_layout(
        xaxis=dict(title="Hour of Day", tickmode="linear"),
        yaxis=dict(
            title="Total Replies",
            gridcolor="rgba(255, 255, 255, 0.1)",
            zeroline=False
        ),
        margin=dict(l=20, r=20, t=30, b=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, Inter, sans-serif", size=12, color="#E0E0E0")
    )
    return fig

def tone_performance_chart(tone_data: dict) -> go.Figure:
    """
    Renders horizontal bar chart for message tone performance.
    """
    tones = list(tone_data.keys())
    rates = list(tone_data.values())
    
    # Capitalize names for formatting
    display_tones = [t.capitalize() for t in tones]
    
    fig = go.Figure(data=[
        go.Bar(
            y=display_tones,
            x=rates,
            orientation="h",
            marker=dict(
                color=["#00CC96", "#33a02c", "#EF553B"],
                line=dict(width=1, color="#1E1E1E")
            ),
            text=[f"{r}%" for r in rates],
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        xaxis=dict(
            title="Reply Rate (%)",
            gridcolor="rgba(255, 255, 255, 0.1)",
            zeroline=False
        ),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=10, b=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, Inter, sans-serif", size=12, color="#E0E0E0")
    )
    return fig
