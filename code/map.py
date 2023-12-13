import dash_leaflet as dl


class Map:
    def __init__(self, db):
        self.db = db
        wms_layer = dl.WMSTileLayer(
            url="https://tiles.maps.eox.at/?",
            layers="s2cloudless-2018_3857",
            format="image/png",
            transparent=False,
        )
        self.heat_layer = []
        self.trajectory_layer = []
        self.map = dl.Map(
            [
                dl.LayersControl(
                    [dl.BaseLayer(wms_layer, name="World Map", checked=True)]
                    + [
                        dl.Overlay(dl.LayerGroup(), name="Heat Map", checked=True),
                        dl.Overlay(dl.LayerGroup(), name="Trajectories", checked=False),
                    ]
                )
            ],
            maxBounds=[[52.617357, 7], [55, 10]],
            zoom=8,
            center=(56, 10),
            id="map",
            minZoom=7,
            style={
                "width": "60%",
                "height": "70vh",
                "margin": "auto",
                "display": "block",
            },
        )

    def load_trajectories(self, zoom_level=0):
        self.trajectory_layer = []
        if zoom_level == 0:
            df = self.db.clustered
        if zoom_level == 1:
            df = self.db.trajectories
        positions = list()
        label = df.head(1).index.get_level_values(0).values[0]
        weight = 1
        for index, row in df.iterrows():
            if label != index[0]:
                opacity = min(float(weight / 600), 1)
                if zoom_level == 1:
                    opacity = 1
                self.trajectory_layer.append(
                    dl.Polyline(
                        positions=positions,
                        color="blue",
                        opacity=opacity,
                        smoothFactor=2,
                    )
                )
                positions = []
                label = index[0]
                weight = 1
            positions.append([row["latitude"], row["longitude"]])
            if zoom_level != 1:
                weight = row["weight"]
        self.map.children[0].children[2].children = [dl.LayerGroup(self.trajectory_layer)]
        return self.map.children

    def add_rect(self, bounds, color, opacity):
        self.heat_layer.append(
            dl.Rectangle(
                bounds=bounds,
                color=color,
                opacity=opacity,
                fillOpacity=opacity,
                stroke=False,
            )
        )

    def render_heatmap(self, rects, max_heat, mbound):
        self.heat_layer = []
        max_heat = max(1, max_heat)
        for i in range(len(rects)):
            rect = rects[i]
            scale = min(1, (rect[1] / max_heat))
            red_min = 255
            red_max = 240
            green_min = 237
            green_max = 59
            blue_min = 160
            blue_max = 32
            red = round(red_min * (1 - scale) + red_max * scale)
            green = round(green_min * (1 - scale) + green_max * scale)
            blue = round(blue_min * (1 - scale) + blue_max * scale)
            color = f"#{red:02x}{green:02x}{blue:02x}"
            if mbound.intersects(rect[0]) and scale != 0:
                self.add_rect(rect[0].to_rect(), color, float(scale != 0) * 0.7)
        self.map.children[0].children[1].children = [dl.LayerGroup(self.heat_layer)]
        return self.map.children

    def clear(self):
        self.heat_layer = []
        self.map.children[0].children[1].children = [dl.LayerGroup()]
