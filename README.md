# 🌊 <ins>Ocean Trajectories Visualizer</ins>

Interactive Dash application for visualizing and analyzing spatio-temporal uncertainties in extrapolated ocean data. 

<br>

### 🔍 <ins>Project Goal</ins>

This project focuses on the detection and visualization of uncertainties in extrapolated oceanographic data, particularly salinity and temperature measurements collected during ferry rides between Büsum and Helgoland in June 2013.<br>
The original in-situ measurements were spatio-temporally extrapolated using current data and simulation models to cover broader areas. However, this extrapolation may introduce inconsistencies, especially when water bodies with significantly different properties are projected to the same or neighboring coordinates.<br>
The core objective is to evaluate the reliability of these derived datasets by identifying and characterizing such contradictions. Two main criteria are considered:

- Spatial proximity between extrapolated points
- Differences in sensor values (e.g., salinity)

Because the thresholds for inconsistencies are context-dependent, the app supports interactive exploration via adjustable parameters (sensor, threshold, time interval). Visual tools such as heatmaps and time series plots help to locate and interpret where and when uncertainties are most prevalent.

<br>

### 🧩 <ins>Key Features</ins>
- 📍 **Interactive Map** with zoom-sensitive heatmap overlays  
- 📊 **Temporal Distribution** of uncertainties across the month  
- 🧪 **Multiple Sensor Support** (Salinity, Temperature, CDOM, etc.)  
- 🎚️ **Dynamic Threshold Control** (Distance & Sensor)  
- 📦 **Trajectory Clustering** for simplified views  
- 📈 **Histograms & Time Series Charts** of sensor values

<br>

### 🖼️ <ins>Preview</ins>

#### 🔧 Main Interface
![main_page](./assets/main_page.png)
**Figure 1:** Main dashboard with selectable parameters for uncertainty detection.<br><br>

#### 🗺️ Spatial Heatmap
![heatmap](./assets/heatmap.png)
**Figure 2:** Heatmap showing grid cells with high density of uncertainties.<br><br>

#### 🔥 Heatmap Parameters
![heatmap_params](./assets/heatmap_parameters.png)
**Figure 3:** Adjust time intervals, sensors, spatial distance, and value thresholds.<br><br>

#### 📉 Temporal Distribution
![nr_uncertainties](./assets/nr_of_uncertainties.png)
**Figure 4:** Number of uncertain extrapolations over time.

<br>

### 🛠️ <ins>Setup & Installation</ins>

```bash
# Clone repository
git clone https://github.com/martin-kunz/ocean-trajectories-visualizer.git
cd ocean-trajectories-visualizer

# (Optional) Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install requirements
pip install -r requirements.txt
```

📂 **Important:** Download the dataset from Google Drive and extract its contents into the `data/` directory:

👉📥 [Download dataset (Google Drive)](https://drive.google.com/uc?export=download&id=1Zr7IrKF20V4V6oAmqFYtbyDg2qCClUAq)

```bash
# After downloading and extracting the data archive
mv path_to_downloaded_data/* ./data/
```

```bash
# Run app
python app.py
```

<br>

### 📁 <ins>Project Structure</ins>

| File / Folder           | Description |
|-------------------------|-------------|
| `app.py`                | Main Dash app logic |
| `map_interface.py`      | Heatmap logic, tree aggregation |
| `database.py`           | Data access, filtering, contradiction detection |
| `interface.py`          | Histogram data access |
| `quadTree.py`           | Quadtree logic for spatial indexing |
| `preprocessing.py`      | Data loading and NetCDF parsing |
| `assets/`               | App styling, logos, images |
| `data/`                 | Sensor & trajectory parquet files (not included) |

<br>

### 📊 <ins>Data Source</ins>

Data is based on [FerryBox Observations by HZG/Hereon](https://www.ferrybox.com/) and includes:
- NetCDF sensor observations (`OBS/obs_2013.nc`)
- Simulated trajectories from June 2013

📝 **Note:** Due to size limitations, original NetCDF datasets are **not included** in this repo.<br>
👉📥 [Download dataset (Google Drive)](https://drive.google.com/uc?export=download&id=1Zr7IrKF20V4V6oAmqFYtbyDg2qCClUAq)

<br>

### 📚 <ins>Research Context</ins>

The goal is to analyze the spatial reliability of simulated water trajectories by identifying inconsistencies in extrapolated salinity and sensor values across small distances.<br>
The spatial logic is implemented via a Time-aware Quadtree, and contradiction detection considers:
- spatial proximity (e.g. ≤ 1km),
- sensor value differences (e.g. > threshold),
- time intervals
