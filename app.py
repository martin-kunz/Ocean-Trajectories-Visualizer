import database
import map_interface
from globals import *
import interface
import sys
import os
from dash import Dash, html, Input, Output, State, dcc, ctx
import dash
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import map

interface_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code")
sys.path.insert(0, interface_path)

db = database.Database()
iface = interface.Interface(db)
i = map_interface.MapInterface(db)
app_map = map.Map(db)

# for initialisation
default_time_end = 10
start_time = datetime.datetime(year=2013, month=6, day=1, hour=0)
end_time = datetime.datetime(year=2013, month=6, day=default_time_end, hour=23)
init_time_dist = i.compute_current_tree("Salinity", 1, start_time, end_time, 1)
rects, max_heat = i.get_rects_and_heat(8)
app_map.render_heatmap(rects, max_heat, default_region)
app_map.load_trajectories(0)


def make_time_distribution(data):
    fig = px.bar(data)
    fig.update_layout(xaxis_title="Time", yaxis_title="Number of uncertainties", showlegend=False)
    return fig


global_plot = make_time_distribution(init_time_dist)

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    use_pages=True,
    suppress_callback_exceptions=True,
)

contra_time_distr = dcc.Graph(id="time_distr", animate=False)

app.layout = html.Div(
    [
        dash.page_container,
        html.Div(
            children=[
                html.P(
                    "Interval (Days)",
                    style={
                        "margin-top": "100px",
                        "margin-bottom": "20px",
                        "font-weight": "bold",
                        "text-decoration": "underline",
                    },
                ),
                dcc.RangeSlider(
                    1,
                    30,
                    value=[1, default_time_end],
                    step=1,
                    id="slider_time_map",
                    allowCross=False,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.P(
                    "Sensor:",
                    style={
                        "margin-top": "50px",
                        "margin-bottom": "20px",
                        "font-weight": "bold",
                        "text-decoration": "underline",
                    },
                ),
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
                    id="dropdown_sensor_map",
                ),
                html.P(
                    "Distance (km):",
                    style={
                        "margin-top": "50px",
                        "margin-bottom": "20px",
                        "font-weight": "bold",
                        "text-decoration": "underline",
                    },
                ),
                dcc.Slider(value=1, id="distance", max=1, min=0),
                html.P(
                    "Threshold:",
                    style={
                        "margin-top": "50px",
                        "margin-bottom": "20px",
                        "font-weight": "bold",
                        "text-decoration": "underline",
                    },
                ),
                dcc.Slider(id="threshold_input", value=1, min=0, max=1),
            ],
            style={
                "margin-top": "50px",
                "margin-bottom": "20px",
                "margin-left": "100px",
                "margin-right": "100px",
            },
        ),
        html.Div(
            children=[
                html.P(
                    "Heatmap:",
                    style={
                        "font-weight": "bold",
                        "text-decoration": "underline",
                    },
                ),
            ],
            style={
                "margin-top": "50px",
                "margin-bottom": "20px",
                "margin-left": "100px",
                "margin-right": "100px",
            },
            id="map-output",
        ),
        app_map.map,
        html.Br(),
        html.Div(
            [
                html.P("Total numbers of uncertainties:",
                       style={
                           "font-weight": "bold",
                           "text-decoration": "underline",
                           "margin-bottom": "10px"
                       },
                       ),
                contra_time_distr
            ],
            style={
                "width": "80%",
                "height": "60vh",
                "margin": "auto",
                "margin-top": "50px"
            }
        )

    ]
)


server = app.server


@app.callback(
    Output("threshold_input", "max"),
    Output("threshold_input", "min"),
    Input("dropdown_sensor_map", "value"),
)
def update_max_threshold(sensor):
    sensors = [
        "Salinity",
        "Temperature",
        "CDOM",
        "Chlorophyll",
        "DO",
        "DOSat",
        "DO_Anomaly",
    ]
    maxs = [13.14, 5.87, 267.6, 54.688, 302.74237, 122.06771, 313.9831]
    mins = [0.12, 0.06069784417908664, 2.694795877619763, 0.4561302076278833, 1.4704905987017072, 0.5743938969588057,
            1.5104531916051702]
    for j in range(len(sensors)):
        if sensor == sensors[j]:
            return maxs[j], mins[j]
    return 1, 0


@app.callback(
    Output("map", "children"),
    Output("time_distr", "figure"),
    [
        Input("threshold_input", "max"),
        Input("map", "zoom"),
        Input("map", "bounds"),
        Input("threshold_input", "value"),
        Input("distance", "value"),
        State("dropdown_sensor_map", "value"),
        Input("slider_time_map", "value"),
    ],
    prevent_initial_call=True,
)
def update_map(_, zoom, mbound, sensor_threshold, distance_threshold, sensor, time):
    global global_plot
    trigger = ctx.triggered_id

    if trigger in ("threshold_input", "dropdown_sensor_map", "slider_time_map", "distance"):
        start_time = datetime.datetime(year=2013, month=6, day=time[0], hour=0)
        end_time = datetime.datetime(year=2013, month=6, day=time[1], hour=23)
        time_distr = i.compute_current_tree(sensor, sensor_threshold, start_time, end_time, distance_threshold)
        rects, max_heat = i.get_rects_and_heat(zoom)
        map_bounds = Region(mbound[0][1], mbound[1][1], mbound[0][0], mbound[1][0])
        global_plot = make_time_distribution(time_distr)
        return app_map.render_heatmap(rects, max_heat, map_bounds), global_plot
    if trigger == "map":
        rects, max_heat = i.get_rects_and_heat(zoom)
        map_bounds = Region(mbound[0][1], mbound[1][1], mbound[0][0], mbound[1][0])
        return app_map.render_heatmap(rects, max_heat, map_bounds), global_plot
    return app_map.map.children, global_plot


@app.callback(
    Output("histogram", "figure"),
    Output("time_distribution_overview", "figure"),
    Input("dropdown_sensor", "value"),
    Input("slider_longitude", "value"),
    Input("slider_latitude", "value"),
    Input("slider_time", "value"),
    Input("checkbox_unique", "value"),
)
def display_graphs(dropdown_sensor, slider_longitude, slider_latitude, slider_time, checkbox_unique):
    # Get data from UI input
    region = Region(*slider_longitude, *slider_latitude)
    start_time = pd.Timestamp(year=2013, month=6, day=slider_time[0], hour=0)
    end_time = pd.Timestamp(year=2013, month=6, day=slider_time[1], hour=23)
    data = iface.get_graph_data(dropdown_sensor, region, start_time, end_time, checkbox_unique)

    # Histogram for sensor value distribution
    if checkbox_unique:
        udata = data.drop_duplicates(subset=["label"])
        fig_hist = px.histogram(udata, x=udata[dropdown_sensor], labels={"x": "Sensor Wert", "y": "Anzahl"})
    else:
        fig_hist = px.histogram(data, x=data[dropdown_sensor], labels={"x": "Sensor Wert", "y": "Anzahl"})

    fig_hist.update_layout(
        xaxis_title=f"{dropdown_sensor} sensor value in {tuple(db.meta[db.meta.long_name == dropdown_sensor].units)[0]}",
        yaxis_title="Number of points",
    )

    # Time Overview Figure
    groups = data[["time", dropdown_sensor]].groupby("time")
    means = groups.mean().sort_values(by="time")
    stdevs = groups.std().sort_values(by="time")[dropdown_sensor].fillna(0)

    time_distr_fig = go.Figure()
    time_distr_fig.add_trace(
        go.Scatter(
            x=means.index,
            y=means[dropdown_sensor] + stdevs,
            mode="lines",
            line=dict(color="rgb(31, 119, 180)", width=0),
            name="Standard deviation",
        )
    )

    time_distr_fig.add_trace(
        go.Scatter(
            x=stdevs.index,
            y=means[dropdown_sensor],
            mode="lines",
            line=dict(color="rgb(31, 119, 180)"),
            fill="tonexty",
            name="Mean",
        )
    )
    time_distr_fig.add_trace(
        go.Scatter(
            x=stdevs.index,
            y=means[dropdown_sensor] - stdevs,
            mode="lines",
            line=dict(color="rgb(31, 119, 180)", width=0),
            fill="tonexty",
            name="Standard deviation negative",
        )
    )

    time_distr_fig.update_layout(
        xaxis_title="Day",
        yaxis_title=f"{dropdown_sensor} sensor value in {tuple(db.meta[db.meta.long_name == dropdown_sensor].units)[0]}",
        hovermode="x",
        showlegend=False,
    )

    return fig_hist, time_distr_fig


if __name__ == "__main__":
    app.run(debug=True)
