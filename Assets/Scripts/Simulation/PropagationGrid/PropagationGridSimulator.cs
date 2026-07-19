using System;
using System.Collections.Generic;
using System.Collections;
using UnityEngine;
using Debug = UnityEngine.Debug;

/// <summary>
/// Builds a 3D voxel grid and stores the received power of each voxel.
/// </summary>
[DefaultExecutionOrder(-900)] // Runs after PatternGainReconstructor
public class PropagationGridSimulator : MonoBehaviour
{

    // --------------------------------------------------
    // Input parameters
    // --------------------------------------------------

    [Header("References")]
    public PropagationSettings settings;
    public PythonBridgeService bridgeService;
    public Transform debugVoxelsParent;
    public PrxVoxelChunkRenderer voxelRenderer;
    public ThresholdSlider thresholdSlider;
    public SimulationLoadingPanel loadingPanel;

    [Header("Grid")]
    public Vector3Int gridSizeMeters = new Vector3Int(10, 10, 10);
    [Min(0.1f)] public float voxelSizeMeters = 1f;
    public bool includeBuildingCollisions = true;

    [Header("Debug")]
    public GameObject voxelDebugPrefab;

    public bool ResultsReady { get; private set; }

    public Vector3Int VoxelCount => GetVoxelCount();

    // Generated voxel data
    public List<VoxelData> voxelsData;

    /// <summary>
    /// Runs the grid simulation sequence and shows loading messages between heavy steps.
    /// </summary>
    private IEnumerator Start()
    {
        ResultsReady = false;

        // Validates loading panel
        if (loadingPanel == null)
        {
            yield break;
        }

        // Validates shared settings
        if (settings == null || !settings.ValidateSetup())
        {
            loadingPanel.Show("Simulation setup error");
            yield break;
        }

        // Validates bridge service
        if (bridgeService == null || !bridgeService.ValidateSetup())
        {
            loadingPanel.Show("Simulation setup error");
            yield break;
        }

        // Validates renderer
        if (voxelRenderer == null)
        {
            loadingPanel.Show("Simulation setup error");
            yield break;
        }

        // Ensures parent object exists
        EnsureParentExists();

        // Builds all voxel positions and prepares the request sent to Python
        loadingPanel.Show("Building voxel grid...");
        yield return null;
        BridgeRequestDto request = BuildGridRequest();

        // Lets Unity update the loading message before calling Python
        BridgeResponseDto response;
        loadingPanel.Show("Computing metrics...");
        yield return null;
        try
        {
            // Sends the grid request through the shared bridge
            response = bridgeService.SendRequest(request);
        }
        catch (Exception ex)
        {
            Debug.LogError($"PropagationGridSimulator: {ex.Message}");
            loadingPanel.Show("Simulation error");
            yield break;
        }

        if (!string.IsNullOrEmpty(response.error))
        {
            Debug.LogError($"PropagationGridSimulator: Python error: {response.error}");
            loadingPanel.Show("Simulation error");
            yield break;
        }

        // Copies the returned values into voxel data
        ApplyResponse(response);
        Debug.Log("PropagationGridSimulator: voxel grid simulation finished.");

        // Lets Unity update the loading message before creating the visible voxels
        loadingPanel.Show("Drawing voxels...");
        yield return null;

        try
        {
            // Builds the renderer chunks with the new voxel data
            voxelRenderer.BuildChunks();

            // Refreshes the threshold label after the Prx range has been calculated
            if (thresholdSlider != null)
            {
                thresholdSlider.RefreshText();
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"PropagationGridSimulator: {ex.Message}");
            loadingPanel.Show("Simulation error");
            yield break;
        }

        // Hides the loading panel when the simulation is ready
        ResultsReady = true;
        loadingPanel.Hide();
        Debug.Log("PropagationGridSimulator: simulation ready.");
    }

    /// <summary>
    /// Clamps grid size values edited in the Inspector.
    /// </summary>
    void OnValidate()
    {
        gridSizeMeters.x = Mathf.Clamp(gridSizeMeters.x, 1, 500);
        gridSizeMeters.y = Mathf.Clamp(gridSizeMeters.y, 1, 200);
        gridSizeMeters.z = Mathf.Clamp(gridSizeMeters.z, 1, 500);
    }

    /// <summary>
    /// Calculates how many voxels fit in each grid axis.
    /// </summary>
    private Vector3Int GetVoxelCount()
    {
        return new Vector3Int(
            Mathf.CeilToInt(gridSizeMeters.x / voxelSizeMeters),
            Mathf.CeilToInt(gridSizeMeters.y / voxelSizeMeters),
            Mathf.CeilToInt(gridSizeMeters.z / voxelSizeMeters)
        );
    }

    /// <summary>
    /// Creates the receiver parent object if none was assigned.
    /// </summary>
    private void EnsureParentExists()
    {
        // Returns when a parent is already assigned
        if (debugVoxelsParent != null)
        {
            return;
        }

        // Creates a default parent object
        GameObject parent = new GameObject("DebugVoxels");
        parent.transform.SetParent(transform, false);
        debugVoxelsParent = parent.transform;
    }

    // --------------------------------------------------
    // Grid generation
    // --------------------------------------------------

    /// <summary>
    /// Builds the voxel list and the grid request sent to Python.
    /// </summary>
    private BridgeRequestDto BuildGridRequest()
    {
        // Calculates the number of voxels in each dimension
        Vector3Int voxelCount = GetVoxelCount();
        int totalVoxels = voxelCount.x * voxelCount.y * voxelCount.z;

        // Initializes voxel data list
        voxelsData = new List<VoxelData>(totalVoxels);

        // Creates the request object sent to Python
        BridgeRequestDto request = settings.BuildBaseRequest();
        request.requestType = "grid";
        request.voxels = new List<GridVoxelRequestDto>(totalVoxels);
        request.receivers = new List<MobileReceiverRequestDto>();


        // Gets the corner of the grid in transmitter local coordinates
        Vector3 localGridOrigin = GetLocalGridOrigin();

        int index = 0;

        // Generates all voxel centers in the 3D grid
        // Note: (YZX) order to make it by horizontal layers
        for (int y = 0; y < voxelCount.y; y++)
        {
            for (int z = 0; z < voxelCount.z; z++)
            {
                for (int x = 0; x < voxelCount.x; x++)
                {
                    // Calculates the center of the current voxel
                    Vector3 localCenter = localGridOrigin + new Vector3((x + 0.5f) * voxelSizeMeters, (y + 0.5f) * voxelSizeMeters, (z + 0.5f) * voxelSizeMeters);

                    // Converts the local voxel center to world coordinates using transmitter rotation
                    Vector3 centerWorldPosition = settings.transmitter.position + settings.transmitter.rotation * localCenter;

                    // Evaluates propagation inputs in Unity
                    string debugLabel = $"Voxel {x},{y},{z} Index={index}";
                    float txGainDbi = settings.EvaluateTxGainDbi(centerWorldPosition, debugLabel);
                    // Counts building collisions and loss if enabled
                    int buildingCollisions = 0;
                    float buildingLossDb = 0f;

                    if (includeBuildingCollisions)
                    {
                        buildingCollisions = settings.CountBuildingCollisions(centerWorldPosition);
                        buildingLossDb = buildingCollisions * settings.GetLossPerWallDb();
                    }

                    // Stores voxel data
                    VoxelData voxel = new VoxelData();
                    voxel.index = index;
                    voxel.gridX = x;
                    voxel.gridY = y;
                    voxel.gridZ = z;
                    voxel.centerWorldPosition = centerWorldPosition;
                    voxel.buildingCollisions = buildingCollisions;
                    voxel.txPowerDbm = settings.txPowerDbm;
                    voxel.txGainDbi = txGainDbi;
                    voxel.rxGainDbi = settings.rxGainDbi;

                    // Adds the voxel data to the list
                    voxelsData.Add(voxel);

                    // Creates debug object if a prefab is assigned
                    if (voxelDebugPrefab != null)
                    {
                        GameObject receiverObject = CreateVoxelDebugObject(x, y, z, centerWorldPosition);

                        VoxelReceiver receiver = receiverObject.AddComponent<VoxelReceiver>();
                        receiver.data = voxel;
                    }

                    // Stores voxel request data for Python
                    GridVoxelRequestDto voxelRequest = new GridVoxelRequestDto();
                    voxelRequest.index = index;
                    voxelRequest.x = centerWorldPosition.x;
                    voxelRequest.y = centerWorldPosition.y;
                    voxelRequest.z = centerWorldPosition.z;
                    voxelRequest.txGainDbi = txGainDbi;
                    voxelRequest.buildingCollisions = buildingCollisions;
                    voxelRequest.buildingLossDb = buildingLossDb;

                    request.voxels.Add(voxelRequest);
                    index++;
                }
            }
        }

        return request;
    }

    /// <summary>
    /// Gets the minimum grid corner in transmitter local coordinates.
    /// </summary>
    private Vector3 GetLocalGridOrigin()
    {
        // Computes the total grid size in meters
        Vector3 gridWorldSize = new Vector3(gridSizeMeters.x, gridSizeMeters.y, gridSizeMeters.z);

        // Returns the minimum corner of the grid in transmitter local coordinates
        return -(gridWorldSize * 0.5f);
    }

    /// <summary>
    /// Creates a debug voxel object for one voxel.
    /// </summary>
    private GameObject CreateVoxelDebugObject(int x, int y, int z, Vector3 centerWorldPosition)
    {
        // Instantiates the debug prefab if available
        if (voxelDebugPrefab != null)
        {
            GameObject debugVoxelObject = Instantiate(voxelDebugPrefab, centerWorldPosition, Quaternion.identity, debugVoxelsParent);
            debugVoxelObject.name = $"VoxelDebug_{x}_{y}_{z}";
            return debugVoxelObject;
        }

        // Creates an empty object when no prefab is assigned
        GameObject emptyDebugVoxel = new GameObject($"VoxelDebug_{x}_{y}_{z}");
        emptyDebugVoxel.transform.SetParent(debugVoxelsParent, false);
        emptyDebugVoxel.transform.position = centerWorldPosition;
        return emptyDebugVoxel;
    }

    /// <summary>
    /// Copies Python grid results into the matching voxel data entries.
    /// </summary>
    private void ApplyResponse(BridgeResponseDto response)
    {
        // Validates response list
        if (response.results == null)
        {
            Debug.LogError("PropagationGridSimulator: Response has no results array.");
            return;
        }

        // Copies each result into the matching voxel data
        for (int i = 0; i < response.results.Count; i++)
        {
            VoxelResultDto result = response.results[i];

            if (result.index < 0 || result.index >= voxelsData.Count)
            {
                Debug.LogWarning($"PropagationGridSimulator: Invalid voxel index in response: {result.index}");
                continue;
            }

            // Copies Python results into voxel data
            VoxelData voxel = voxelsData[result.index];
            voxel.distanceMeters = result.distanceMeters;
            voxel.pathLossDb = result.pathLossDb;
            voxel.prxDbm = result.prxDbm;
        }
    }

}
