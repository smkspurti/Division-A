import plotly.graph_objects as go
import plotly.express as px

def feasibility_bar_chart(ideas):
    titles = [f"#{i['rank']} {i['title'][:25]}..." if len(i['title']) > 25 else f"#{i['rank']} {i['title']}" for i in ideas]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Feasibility", x=titles, y=[i["feasibility_score"] for i in ideas], marker_color="#6366f1"))
    fig.add_trace(go.Bar(name="Innovation", x=titles, y=[i["innovation_score"] for i in ideas], marker_color="#22d3ee"))
    fig.add_trace(go.Bar(name="Impact", x=titles, y=[i["impact_score"] for i in ideas], marker_color="#f59e0b"))
    fig.update_layout(
        barmode="group",
        title="Project Ideas — Score Comparison",
        yaxis=dict(range=[0, 10], title="Score (out of 10)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=60),
        font=dict(size=12)
    )
    return fig

def radar_chart(idea):
    categories = ["Feasibility", "Innovation", "Impact"]
    values = [idea["feasibility_score"], idea["innovation_score"], idea["impact_score"]]
    values += values[:1]
    categories += categories[:1]
    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(99,102,241,0.2)",
        line=dict(color="#6366f1", width=2)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        title=f"Top Idea Profile: {idea['title'][:30]}",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        margin=dict(t=50, b=20)
    )
    return fig

def skill_gap_gauge(readiness_score):
    color = "#22c55e" if readiness_score >= 70 else "#f59e0b" if readiness_score >= 40 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=readiness_score,
        title={"text": "Skill Readiness"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                {"range": [70, 100], "color": "rgba(34,197,94,0.15)"}
            ]
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=20), height=250)
    return fig

def risk_pie_chart(risks):
    labels = [r["category"] for r in risks]
    prob_map = {"High": 3, "Medium": 2, "Low": 1}
    values = [prob_map.get(r["probability"], 2) for r in risks]
    colors = ["#ef4444", "#f59e0b", "#6366f1", "#22d3ee", "#22c55e"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors[:len(labels)]),
        hole=0.4
    ))
    fig.update_layout(
        title="Risk Distribution by Category",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=20),
        font=dict(size=12)
    )
    return fig
