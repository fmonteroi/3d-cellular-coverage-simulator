# 3D Cellular Coverage Simulator

A tool for analysing and visualising radio coverage in an urban environment. It combines an application developed in **Unity** with a **Python** propagation engine, using the Centro Universitario de Mérida campus as a case study.

The project accompanies the manuscript **A Lightweight Digital Twin Framework for Three-Dimensional Coverage Assessment of Urban Cellular Deployments**, by Francisco Montero Sánchez, José Javier Rico Palomo and Francisco Díaz Barrancas.

## Download precompiled Windows version

A precompiled 64-bit Windows version is available from the GitHub Releases page:

[Download the latest release](https://github.com/fmonteroi/3d-cellular-coverage-simulator/releases/latest)

The precompiled version includes the Unity application and the portable Python runtime, so Unity Editor and a separate Python installation are not required to run it.

> **Source project only:** the campus model is distributed separately. Download it and add it to the project by following the installation instructions before opening the project in Unity.

## Features

- Reconstruction of a panel antenna's 3D radiation pattern from its horizontal and vertical cuts using the Gil and Vasiliadis methods, and comparison with an omnidirectional model.
- Path-loss calculation using the FSPL and ABG models, with additional building penetration losses.
- Received-power visualisation through a 3D heat map and 2D views at different height layers.
- Mobile receivers following three routes: a vehicle travelling around the campus, a vehicle following a straight path, and a pedestrian.
- Monitoring of received power and signal-to-noise ratio (SNR) for mobile receivers.
- Configurable simulation parameters, visualisation threshold and performance modes.
- Export of configuration, reconstructed pattern and metrics, with automatic plot generation.

## Requirements

### Precompiled version

- **64-bit Windows**.
- No Unity or separate Python installation is required.

### Source project

- **64-bit Windows**: the bundled Python interpreter and dependencies target this platform.
- **Unity Hub and Unity Editor 6000.3.6f1**, the version specified in `ProjectSettings/ProjectVersion.txt`.
- An Internet connection to download the campus model and restore Unity packages when opening the project for the first time.

The repository includes a **portable Python runtime** and its dependencies: there is no need to install Python separately or start the server manually.

## Installation

### 1. Download the repository

Clone the project:

```bash
git clone https://github.com/fmonteroi/3d-cellular-coverage-simulator.git
cd 3d-cellular-coverage-simulator
```

Alternatively, download it from GitHub using **Code → Download ZIP** and extract the archive.

### 2. Add the campus model

[Download the campus assets](https://unexes-my.sharepoint.com/personal/jjricopal_unex_es/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fjjricopal%5Funex%5Fes%2FDocuments%2FAssets%2D20260929T092504Z%2D1%2D001%2Ezip&parent=%2Fpersonal%2Fjjricopal%5Funex%5Fes%2FDocuments&ga=1)

With the Unity Editor closed:

1. Download and extract the ZIP archive.
2. Locate the `Campus` folder inside the downloaded package's `Assets` folder.
3. Copy the entire `Campus` folder into the repository's `Assets/Models/` directory.

The resulting directory structure should be:

```text
3d-cellular-coverage-simulator/
├── Assets/
│   ├── Models/
│   │   ├── Campus.meta
│   │   └── Campus/
│   │       ├── ExtractedTextures/
│   │       ├── Materials/
│   │       ├── Model/
│   │       │   ├── CAMPUS.fbx
│   │       │   ├── CAMPUS.fbx.meta
│   │       │   ├── COLLISIONS.fbx
│   │       │   └── COLLISIONS.fbx.meta
│   │       └── Textures/
│   ├── Scenes/
│   ├── Scripts/
│   └── StreamingAssets/
├── Packages/
└── ProjectSettings/
```

**Do not copy `Campus` directly into `Assets/` or create an `Assets/Assets/` folder.** The destination is `Assets/Models/Campus/`. The package includes both visual and collision geometry, together with the associated assets.

### 3. Open and run

1. In Unity Hub, add the project root folder containing `Assets`, `Packages` and `ProjectSettings`.
2. Open it with **Unity 6000.3.6f1** and wait for assets and packages to finish importing.
3. Open `Assets/Scenes/MainMenu.unity`.
4. Press **Play** and open the simulation settings.
5. Select the link parameters, grid settings, and visualisation and output options.
6. Start the simulation. Unity automatically launches the local Python server and requests the grid calculation before updating the mobile receivers.

For an initial run on a machine with limited resources, use a small grid or larger voxels. The number of voxels affects computation time and memory usage.

## Results

Each run creates a `Results/<timestamp>/` folder:

- In the Editor, under the project root.
- In a standalone build, alongside the executable.

This folder contains:

- `simulation_config.txt`: the configuration used for the run.
- `reconstructed_pattern.csv`: the radiation pattern used.
- One CSV per mobile receiver containing time, distance, received power, SNR, position, transmit antenna gain, path loss and collision count.
- The PNG plots selected in the configuration menu.

Receiver data is exported when the first route traversal is completed; pending records are exported on exit. Plots are generated automatically from these CSV files.

## Scope and limitations

The simulator studies propagation and link metrics. It does not implement a complete 5G network or V2X protocols.

- A single transmitter is used; SNR is calculated without interference from other transmitters.
- The FSPL and ABG models are supplemented with simplified concrete-wall penetration losses. Reflections and diffraction are not simulated using electromagnetic ray tracing.
- The grid uses reference receivers with a gain of 0 dBi; each voxel represents the value calculated at its centre.
- The campus geometry and reconstructed pattern are approximations. The system is not synchronised with real-time field measurements.
- The colour scale is normalised for each simulation: when comparing configurations, use numerical values and CSV files as well as images.

## Authors and related work

This project was developed at the Universidad de Extremadura with contributions from:

- Francisco Montero Sánchez
- José Javier Rico Palomo
- Francisco Díaz Barrancas

Related manuscript:

> Francisco Montero Sánchez, José Javier Rico Palomo and Francisco Díaz Barrancas. *A Lightweight Digital Twin Framework for Three-Dimensional Coverage Assessment of Urban Cellular Deployments*.

The propagation engine, Python interpreter, dependencies and third-party assets retain their respective authorship and terms of use.
