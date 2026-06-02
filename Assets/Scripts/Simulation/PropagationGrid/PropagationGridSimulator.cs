using System;
using System.Collections.Generic;
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
    public Transform receiversParent;

    [Header("Grid")]
    public Vector3Int gridSizeMeters = new Vector3Int(10, 10, 10);
    [Min(0.1f)] public float voxelSizeMeters = 1f;
    public bool includeBuildingCollisions = true;

    [Header("Debug")]
    public GameObject receiverDebugPrefab;

    // Ready flag
    public bool ResultsReady { get; private set; }

    // Generated voxel data
    public List<VoxelData> voxelsData;

    void Start()
    {
        ResultsReady = false;

        // Validate shared settings
        if (settings == null || !settings.ValidateSetup())
        {
            return;
        }

        // Validate bridge service
        if (bridgeService == null || !bridgeService.ValidateSetup())
        {
            return;
        }

        // Ensure parent object exists
        EnsureParentExists();

        // Build the grid request
        BridgeRequestDto request = BuildGridRequest();

        try
        {
            // Send the grid request through the shared bridge
            BridgeResponseDto response = bridgeService.SendRequest(request);

            if (!string.IsNullOrEmpty(response.error))
            {
                Debug.LogError($"PropagationGridSimulator: Python error: {response.error}");
                return;
            }

            // Copy the returned values into voxel data
            ApplyResponse(response);

            ResultsReady = true;
            Debug.Log("PropagationGridSimulator: voxel grid simulation finished.");

            PrxVoxelChunkRenderer renderer = FindFirstObjectByType<PrxVoxelChunkRenderer>();

            if (renderer != null)
            {
                renderer.BuildChunks();
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"PropagationGridSimulator: {ex.Message}");
        }
    }

    void OnValidate()
    {
        gridSizeMeters.x = Mathf.Clamp(gridSizeMeters.x, 1, 200);
        gridSizeMeters.y = Mathf.Clamp(gridSizeMeters.y, 1, 200);
        gridSizeMeters.z = Mathf.Clamp(gridSizeMeters.z, 1, 200);
    }

    private Vector3Int GetVoxelCount()
    {
        return new Vector3Int(
            Mathf.CeilToInt(gridSizeMeters.x / voxelSizeMeters),
            Mathf.CeilToInt(gridSizeMeters.y / voxelSizeMeters),
            Mathf.CeilToInt(gridSizeMeters.z / voxelSizeMeters)
        );
    }

    private void EnsureParentExists()
    {
        // If parent already assigned, it returns
        if (receiversParent != null)
        {
            return;
        }

        // Creates a default parent object
        GameObject parent = new GameObject("SimulatedReceivers");
        parent.transform.SetParent(transform, false);
        receiversParent = parent.transform;
    }

    // --------------------------------------------------
    // Grid generation
    // --------------------------------------------------

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
                    // Center of the current voxel
                    Vector3 localCenter = localGridOrigin + new Vector3((x + 0.5f) * voxelSizeMeters, (y + 0.5f) * voxelSizeMeters, (z + 0.5f) * voxelSizeMeters);

                    // Converts the local voxel center to world coordinates using transmitter rotation
                    Vector3 center = settings.transmitter.position + settings.transmitter.rotation * localCenter;

                    // Evaluates propagation inputs in Unity
                    string debugLabel = $"Voxel {x},{y},{z} Index={index}";
                    float txGainDbi = settings.EvaluateTxGainDbi(center, debugLabel);
                    // Counts building collisions and loss if enabled
                    int buildingCollisions = 0;
                    float buildingLossDb = 0f;

                    if (includeBuildingCollisions)
                    {
                        buildingCollisions = settings.CountBuildingCollisions(center);
                        buildingLossDb = buildingCollisions * settings.lossPerBuildingDb;
                    }

                    // Store voxel data
                    VoxelData sample = new VoxelData();
                    sample.index = index;
                    sample.gridX = x;
                    sample.gridY = y;
                    sample.gridZ = z;
                    sample.centerWorldPosition = center;
                    sample.buildingCollisions = buildingCollisions;
                    sample.txPowerDbm = settings.txPowerDbm;
                    sample.txGainDbi = txGainDbi;
                    sample.rxGainDbi = settings.rxGainDbi;

                    // Adds the voxeldata to the list
                    voxelsData.Add(sample);

                    // Creates debug object if a prefab is assigned
                    if (receiverDebugPrefab != null)
                    {
                        GameObject receiverObject = CreateReceiverObject(x, y, z, center);

                        VoxelReceiver receiver = receiverObject.AddComponent<VoxelReceiver>();
                        receiver.data = sample;
                    }

                    // Stores voxel request data for Python
                    GridVoxelRequestDto voxelRequest = new GridVoxelRequestDto();
                    voxelRequest.index = index;
                    voxelRequest.x = center.x;
                    voxelRequest.y = center.y;
                    voxelRequest.z = center.z;
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

    private Vector3 GetLocalGridOrigin()
    {
        // Computes the total grid size in meters
        Vector3 gridWorldSize = new Vector3(gridSizeMeters.x, gridSizeMeters.y, gridSizeMeters.z);

        // Returns the minimum corner of the grid in transmitter local coordinates
        return -(gridWorldSize * 0.5f);
    }

    private GameObject CreateReceiverObject(int x, int y, int z, Vector3 center)
    {
        // Instantiates the debug prefab if available
        if (receiverDebugPrefab != null)
        {
            GameObject receiverObject = Instantiate(receiverDebugPrefab, center, Quaternion.identity, receiversParent);
            receiverObject.name = $"Rx_{x}_{y}_{z}";
            return receiverObject;
        }

        // Otherwise create an empty object
        GameObject emptyReceiver = new GameObject($"Rx_{x}_{y}_{z}");
        emptyReceiver.transform.SetParent(receiversParent, false);
        emptyReceiver.transform.position = center;
        return emptyReceiver;
    }


    private void ApplyResponse(BridgeResponseDto response)
    {
        // Validate response list
        if (response.results == null)
        {
            Debug.LogError("PropagationGridSimulator: Response has no results array.");
            return;
        }

        // Copy each result into the matching voxel data
        for (int i = 0; i < response.results.Count; i++)
        {
            VoxelResultDto result = response.results[i];

            if (result.index < 0 || result.index >= voxelsData.Count)
            {
                Debug.LogWarning($"PropagationGridSimulator: Invalid voxel index in response: {result.index}");
                continue;
            }

            // Copy Python results into voxel data
            VoxelData sample = voxelsData[result.index];
            sample.distanceMeters = result.distanceMeters;
            sample.pathLossDb = result.pathLossDb;
            sample.prxDbm = result.prxDbm;
        }
    }

}
