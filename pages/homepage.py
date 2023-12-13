import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/")


layout = dbc.Container(
    [
        html.Div(
            children=[
                html.Br(),
                html.Img(
                    src=dash.get_asset_url("logo.png"),
                    height=140,
                    width=160,
                    style={"float": "right"},
                ),
                html.Br(),
                html.H2("Sea Trajectories", className="Header", style={"margin-bottom": "40px"}),
                html.Br(),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.P("Longitude:", style={"font-weight": "bold", "text-decoration": "underline"}),
                                dcc.RangeSlider(
                                    7.2,
                                    9.5,
                                    value=[7.9, 7.92],
                                    id="slider_longitude",
                                    allowCross=False,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                                html.Br(),
                                html.P("Latitude:", style={"font-weight": "bold", "text-decoration": "underline"}),
                                dcc.RangeSlider(
                                    53.5,
                                    54.6,
                                    value=[54.1, 54.15],
                                    id="slider_latitude",
                                    allowCross=False,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                                html.Br(),
                                html.P("Interval (Days)", style={"font-weight": "bold", "text-decoration": "underline"}),
                                dcc.RangeSlider(
                                    1,
                                    30,
                                    value=[1, 10],
                                    step=1,
                                    id="slider_time",
                                    allowCross=False,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                            ],
                            style={"flex": 1},
                        ),
                        html.Div(
                            children=[
                                html.P("Sensor:", style={"font-weight": "bold", "text-decoration": "underline"}),
                                dcc.Dropdown(
                                    {
                                        "Salinity": "Salinity",
                                        "Temperature": "Temperature",
                                        "CDOM": "Colored dissolved organic matter (CDOM)",
                                        "Chlorophyll": "Chlorophyll",
                                        "DO": "Dissolved Oxygen (DO)",
                                        "DOSat": "DO Saturation",
                                        "DO_Anomaly": "DO Anomaly",
                                    },
                                    "Salinity",
                                    id="dropdown_sensor",
                                ),
                                html.Br(),
                                html.Br(),
                                dcc.Checklist(
                                    options=[{"label": "One point per trajectory in the histogram", "value": True}], value=[True], id="checkbox_unique"
                                ),
                            ],
                            style={"flex": 1},
                        ),
                    ],
                    style={"display": "flex", "flex-direction": "row"},
                ),
                html.Br(),
                html.Div(
                    [
                        dcc.Graph(id="time_distribution_overview"),
                    ],
                    style={"width": "49%", "display": "inline-block"},
                ),
                html.Div([dcc.Graph(id="histogram")], style={"width": "49%", "display": "inline-block"}),
            ]
        ),
    ]
)
